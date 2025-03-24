import os
import shutil
import json
import logging
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query, Path
from ..models.file import FileResponse
from ..database import prisma
from ..utils.auth import get_current_user
from ..models.user import UserResponse as User
from ..core.document_loader import load_document_to_text
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = "public/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file types
SUPPORTED_FILE_TYPES = {
    '.pdf': 'pdf',
    '.csv': 'csv',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.pptx': 'ppt',
    '.ppt': 'ppt',
    '.docx': 'docx',
    '.doc': 'docx'
}

def validate_file_type(file: UploadFile) -> bool:
    """
    Kiểm tra xem file có phải là loại được hỗ trợ không (PDF hoặc CSV).
    
    Parameters:
        file: File cần kiểm tra
        
    Returns:
        True nếu file là PDF hoặc CSV, False nếu không phải
    """
    _, file_extension = os.path.splitext(file.filename.lower())
    return file_extension in SUPPORTED_FILE_TYPES

def get_file_size(file_path: str) -> int:
    """
    Lấy kích thước của file theo byte.
    
    Parameters:
        file_path: Đường dẫn đến file
        
    Returns:
        Kích thước file tính bằng byte
    """
    return os.path.getsize(file_path)

@router.post("/upload", response_model=List[FileResponse])
async def upload_file(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Tải lên một hoặc nhiều tệp (PDF, CSV, Excel, PowerPoint, Word), lưu cục bộ, trích xuất văn bản và lưu trữ trong cơ sở dữ liệu.
    Sau đó nhúng nội dung văn bản vào ChromaDB để hỗ trợ trò chuyện với tài liệu.

    Tham số:
    files: Danh sách các tệp để tải lên (hỗ trợ PDF, CSV, Excel, PowerPoint, Word)
    messageId: id của tin nhắn tệp này thuộc về (tùy chọn)
    current_user: người dùng được xác thực hiện tại

    Trả lại:
    Danh sách các đối tượng tệp với siêu dữ liệu và văn bản trích xuất

    Tăng:
    400: Nếu không có tệp hợp lệ nào được tải lên hoặc tệp không phải PDF/CSV
    404: Nếu không tìm thấy trò chuyện
    403: Nếu người dùng không sở hữu cuộc trò chuyện
    """
    # Validate file types first
    valid_files = []
    for file in files:
        if validate_file_type(file):
            valid_files.append(file)
        else:
            logger.warning(f"Skipping unsupported file: {file.filename} (supported types: {', '.join(SUPPORTED_FILE_TYPES.keys())})")
    
    # If no valid files, return error immediately
    if not valid_files:
        raise HTTPException(
            status_code=400, 
            detail=f"No valid files were uploaded. Only {', '.join(SUPPORTED_FILE_TYPES.keys())} files are supported."
        )
    

    # Create user-specific directory
    user_upload_dir = os.path.join(UPLOAD_DIR, current_user.id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    uploaded_files = []
    
    for file in valid_files:
        file_path = None
        try:
            # Get file extension
            _, file_extension = os.path.splitext(file.filename.lower())
            file_type = SUPPORTED_FILE_TYPES[file_extension]
            
            # Save file to disk
            file_path = os.path.join(user_upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size in bytes
            file_size = get_file_size(file_path)
            
            # Extract text from file based on its type
            text_content = []
            
            # Xử lý đặc biệt cho CSV với tham số tùy chỉnh
            if file_extension == '.csv':
                # Default CSV arguments - can be customized if needed
                csv_args = {"delimiter": ",", "quotechar": '"'}
                text_content = load_document_to_text(file_path, file_type=file_type, csv_args=csv_args)
            else:
                # Xử lý các loại file khác
                text_content = load_document_to_text(file_path, file_type=file_type)
                
            # Join all content into a single text
            full_text = "\n\n".join(text_content) if text_content else ""
            
            # Save file metadata and content to database
            db_file = await prisma.file.create(
                data={
                    "filename": file.filename,
                    "filepath": file_path,
                    "filetype": file_type,  # Store file type
                    "size": file_size,      # Add file size in bytes
                    "metadata": "{}"        # Initialize empty metadata as JSON string
                }
            )
        
            # Embed and store document in ChromaDB for future conversations
            try:
                # Thêm metadata cho tài liệu
                metadata = {
                    "filename": file.filename,
                    "filetype": file_type,
                    "size": file_size,
                    "uploaded_by": current_user.id,
                    "upload_date": datetime.now().isoformat(),
                }
                
                # Gọi hàm embed_and_store_document từ agents.py để nhúng và lưu trữ tài liệu
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
                
                logger.info(f"Successfully embedded file {file.filename} with collection ID: {collection_id}")
            except Exception as e:
                # Log lỗi nhưng không làm gián đoạn quá trình tải lên
                logger.error(f"Error embedding file {file.filename}: {str(e)}")
                # Vẫn trả về file đã tải lên thành công, nhưng không có khả năng trò chuyện
            
            uploaded_files.append(db_file)
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            # Xóa file đã lưu nếu xử lý thất bại
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up file {file_path}: {str(cleanup_error)}")
    
    if not uploaded_files:
        raise HTTPException(
            status_code=500, 
            detail="Failed to process any of the uploaded files. Please check the logs for details."
        )
    
    return uploaded_files

@router.delete("/{file_id}", response_model=dict)
async def delete_file(
    file_id: str = Path(..., description="ID của file cần xóa"),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa file từ database, xóa file local và xóa vector trong ChromaDB.
    
    Tham số:
    file_id: ID của file cần xóa
    current_user: người dùng được xác thực hiện tại
    
    Trả lại:
    Thông báo xác nhận xóa thành công
    
    Tăng:
    404: Nếu không tìm thấy file
    403: Nếu người dùng không có quyền xóa file
    500: Nếu có lỗi xảy ra trong quá trình xóa
    """
    # Tìm file trong database
    db_file = await prisma.file.find_unique(where={"id": file_id})
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Lấy thông tin metadata
    metadata = {}
    collection_id = None
    
    if db_file.metadata:
        try:
            metadata = json.loads(db_file.metadata)
            collection_id = metadata.get("collection_id")
        except json.JSONDecodeError:
            logger.error(f"Error parsing metadata JSON for file {file_id}")
    
    # Xóa vector trong ChromaDB nếu có collection_id
    if collection_id:
        try:
            from app.core.config import ChatAgentConfig as config
            chroma_dir = os.path.join(config.CHROMA_PERSIST_DIRECTORY, collection_id)
            
            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir)
                logger.info(f"Deleted ChromaDB collection: {collection_id}")
            else:
                logger.warning(f"ChromaDB collection directory not found: {chroma_dir}")
        except Exception as e:
            logger.error(f"Error deleting ChromaDB collection: {str(e)}")
            # Tiếp tục xóa file ngay cả khi không thể xóa collection
    
    # Nếu không có collection_id, tìm kiếm dựa trên source_file_id
    if not collection_id:
        try:
            from app.core.config import ChatAgentConfig as config
            # Tìm tất cả các thư mục collection có chứa source_file_id
            collection_dirs = [d for d in os.listdir(config.CHROMA_PERSIST_DIRECTORY) 
                            if os.path.isdir(os.path.join(config.CHROMA_PERSIST_DIRECTORY, d)) 
                            and d.startswith(f"doc_{file_id}_")]
            
            # Xóa tất cả các collection tìm thấy
            for dir_name in collection_dirs:
                chroma_dir = os.path.join(config.CHROMA_PERSIST_DIRECTORY, dir_name)
                shutil.rmtree(chroma_dir)
                logger.info(f"Deleted ChromaDB collection: {dir_name}")
        except Exception as e:
            logger.error(f"Error searching and deleting ChromaDB collections: {str(e)}")
    
    # Xóa file local nếu tồn tại
    if db_file.filepath and os.path.exists(db_file.filepath):
        try:
            os.remove(db_file.filepath)
            logger.info(f"Deleted local file: {db_file.filepath}")
        except Exception as e:
            logger.error(f"Error deleting local file: {str(e)}")
            # Tiếp tục xóa bản ghi trong database ngay cả khi không thể xóa file local
    
    # Xóa bản ghi file trong database
    try:
        await prisma.file.delete(where={"id": file_id})
        logger.info(f"Deleted file record from database: {file_id}")
    except Exception as e:
        logger.error(f"Error deleting file record from database: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting file record from database: {str(e)}"
        )
    
    return {"message": "File deleted successfully", "file_id": file_id}
