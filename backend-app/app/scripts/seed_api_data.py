from datetime import datetime
import json
import logging
import asyncio
import os
import aiohttp
import shutil
from typing import Tuple, List, Dict, Any, Optional

from app.core.document_loader import load_document_to_text
from ..core.config import ChatAgentConfig
from ..database import prisma



# Cấu hình logging
logger = logging.getLogger(__name__)

async def login_to_api() -> Tuple[bool, str]:
    """
    Đăng nhập vào API để lấy token xác thực.
    
    Trả về:
        Tuple chứa trạng thái thành công và token hoặc thông báo lỗi
    """
    try:
        login_url = "https://id.asgl.net.vn/api/auth/login"
        login_data = {
            "login": "asgl-01940",
            "password": "66668889"
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(login_url, data=login_data) as response:
                if response.status != 200:
                    return False, f"Đăng nhập thất bại với mã lỗi: {response.status}"
                
                try:
                    data = await response.json()
                    if not data.get("success", False):
                        return False, data.get("message", "Đăng nhập thất bại")
                    
                    token = data.get("data", {}).get("token")
                    if not token:
                        return False, "Không tìm thấy token trong phản hồi"
                    
                    return True, token
                except json.JSONDecodeError:
                    return False, "Phản hồi không hợp lệ từ API đăng nhập"
    
    except Exception as e:
        logger.error(f"Lỗi khi đăng nhập: {str(e)}")
        return False, f"Lỗi khi đăng nhập: {str(e)}"
    

async def get_data_api_with_link_by_config_and_embbedding() -> List[Dict[str, Any]]:
    """
    Lấy dữ liệu từ API theo cấu hình, lưu trữ và nhúng dữ liệu để sử dụng trong trò chuyện.
    
    Quy trình:
    1. Kết nối đến Prisma
    2. Đăng nhập để lấy token xác thực
    3. Lấy dữ liệu từ các API được cấu hình
    4. Lưu dữ liệu dưới dạng file JSON
    5. Trích xuất nội dung văn bản từ file JSON
    6. Lưu metadata và nội dung vào database
    7. Nhúng và lưu trữ tài liệu trong ChromaDB
    
    Returns:
        List[Dict[str, Any]]: Danh sách các file đã xử lý với thông tin chi tiết
    """
    # Connect to Prisma client first
    await prisma.connect()
   
    # Tạo thư mục lưu trữ
    upload_dir = os.path.join(ChatAgentConfig.UPLOAD_DIR, "json_api_data")
    # Xóa thư mục cũ nếu tồn tại để tránh dữ liệu trùng lặp
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # Lấy cấu hình API từ config
    data_api_fetching = ChatAgentConfig.dataApiFetching
    
    # Đăng nhập để lấy token
    success, token_or_error = await login_to_api()
    
    if not success:
        logger.error(f"Login failed: {token_or_error}")
        return []
    
    # Danh sách lưu trữ kết quả xử lý
    processed_files = []
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for api in data_api_fetching:
                url = f"{api['url']}"
                headers = {
                    "Authorization": f"Bearer {token_or_error}",
                    "Content-Type": "application/json",
                }

                try:
                    # Gọi API để lấy dữ liệu
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch data from {url} with status code {response.status}")
                            continue
                            
                        data = await response.json()
                        
                        # Lưu dữ liệu vào file JSON
                        filename = f"{api['value']}.json"
                        file_path = os.path.join(upload_dir, filename)
                        with open(file_path, "w") as json_file:
                            json.dump(data, json_file)
                        
                        # Lấy kích thước file
                        file_size = os.path.getsize(file_path)
                        
                        # Trích xuất nội dung văn bản từ file JSON
                        try:
                            # Sử dụng hàm load_document_to_text với tham số phù hợp cho JSON
                            text_content = load_document_to_text(
                                file_path, 
                                file_type="json", 
                                text_content=False
                            )
                            
                            # Chuyển đổi nội dung thành văn bản
                            if text_content and isinstance(text_content, list):
                                full_text = "\n\n".join(str(item) for item in text_content if item)
                            else:
                                full_text = str(text_content) if text_content else ""
                            
                            # Nếu không có nội dung, chuyển đổi trực tiếp từ JSON
                            if not full_text:
                                full_text = json.dumps(data, indent=2)
                                
                            # Kiểm tra nội dung trước khi tiếp tục
                            if not full_text:
                                logger.warning(f"Empty text content for {filename}, skipping embedding")
                                continue
                                
                        except Exception as e:
                            logger.error(f"Error extracting text from JSON file {filename}: {str(e)}")
                            # Fallback to plain JSON string if extraction fails
                            full_text = json.dumps(data, indent=2)

                        # Lưu metadata và nội dung vào database
                        db_file = await prisma.file.create(
                            data={
                                "filename": filename,
                                "filepath": file_path,
                                "filetype": "json",
                                "size": file_size,
                                "metadata": "{}"  # Initialize empty metadata as JSON string
                            }
                        )
                        
                        # Nhúng và lưu trữ tài liệu trong ChromaDB
                        try:
                            # Tạo metadata cho tài liệu
                            metadata = {
                                "filename": filename,
                                "filetype": "json",
                                "size": file_size,
                                "upload_date": datetime.now().isoformat(),
                                "source": "api",
                                "api_name": api['value']
                            }
                            
                            # Gọi hàm embed_and_store_document để nhúng và lưu trữ tài liệu
                            from app.core.agents import embed_and_store_document
                            collection_id = await embed_and_store_document(
                                text=full_text,
                                source_file_id=db_file.id,
                                metadata=metadata
                            )
                            
                            # Cập nhật thông tin file trong database với collection_id
                            metadata_json = json.dumps({"collection_id": collection_id})
                            db_file = await prisma.file.update(
                                where={"id": db_file.id},
                                data={"metadata": metadata_json}
                            )
                            
                            logger.info(f"Successfully embedded file {filename} with collection ID: {collection_id}")
                            
                            # Thêm vào danh sách kết quả
                            processed_files.append({
                                "id": db_file.id,
                                "filename": filename,
                                "filetype": "json",
                                "size": file_size,
                                "collection_id": collection_id
                            })
                            
                        except Exception as e:
                            logger.error(f"Error embedding file {filename}: {str(e)}")
                            # Vẫn thêm vào danh sách kết quả nhưng không có collection_id
                            processed_files.append({
                                "id": db_file.id,
                                "filename": filename,
                                "filetype": "json",
                                "size": file_size,
                                "error": str(e)
                            })
                            
                except Exception as e:
                    logger.error(f"Error processing API {api['value']}: {str(e)}")
                    
            logger.info(f"Processed {len(processed_files)} API endpoints successfully")
            return processed_files
            
    except Exception as e:
        logger.error(f"Error in API data fetching process: {str(e)}")
        return []
        
    finally:
        # Đảm bảo ngắt kết nối Prisma khi hoàn thành
        await prisma.disconnect()


def main():
    """
    Hàm chính để chạy quá trình lấy dữ liệu API.
    """
    result = asyncio.run(get_data_api_with_link_by_config_and_embbedding())
    if result:
        logger.info(f"Successfully processed {len(result)} API endpoints")
    else:
        logger.warning("No API endpoints were processed successfully")

if __name__ == "__main__":
    main()



