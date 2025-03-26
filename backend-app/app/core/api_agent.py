import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .config import ChatAgentConfig as config

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

async def generate_response_from_api(answer: str, url_api: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Tạo phản hồi dựa trên dữ liệu từ API và câu hỏi của người dùng.
    
    Tham số:
        answer: Câu hỏi của người dùng
        url_api: URL của API cần truy vấn
        chat_history: Lịch sử trò chuyện (tùy chọn)
        
    Trả về:
        Phản hồi của trợ lý AI dựa trên dữ liệu API
    """
    try:
        # Kiểm tra URL hợp lệ
        if not url_api.startswith(('http://', 'https://')):
            return config.ERROR_MESSAGES.get("invalid_url", "Invalid URL format")
        
        # Đăng nhập để lấy token
        success, token_or_error = await login_to_api()
        if not success:
            return config.ERROR_MESSAGES.get("auth_error", "Authentication error: {error}").format(error=token_or_error)
        
        token = token_or_error
            
        # Cấu hình timeout cho request
        timeout = aiohttp.ClientTimeout(total=30)
        
        # Lấy dữ liệu từ API với retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {token}"
                }
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url_api, headers=headers) as response:
                        if response.status == 401:  # Unauthorized
                            # Thử đăng nhập lại nếu token hết hạn
                            if attempt < max_retries - 1:
                                success, token_or_error = await login_to_api()
                                if not success:
                                    return config.ERROR_MESSAGES.get("auth_error", "Authentication error: {error}").format(error=token_or_error)
                                token = token_or_error
                                continue
                            return config.ERROR_MESSAGES.get("auth_error", "Authentication failed")
                            
                        if response.status == 429:  # Too Many Requests
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            return config.ERROR_MESSAGES.get("rate_limit", "Rate limit exceeded")
                            
                        if response.status != 200:
                            return config.ERROR_MESSAGES.get("api_error", "API error: {error}").format(
                                error=f"API trả về status code {response.status}"
                            )
                        
                        # Xử lý dữ liệu JSON với validation
                        try:
                            data = await response.json()
                            if not isinstance(data, (dict, list)):
                                return config.ERROR_MESSAGES.get("invalid_data", "Invalid data format")
                        except json.JSONDecodeError:
                            return config.ERROR_MESSAGES.get("invalid_json", "Invalid JSON response")
                        
                        # Tối ưu hóa context bằng cách lọc dữ liệu không cần thiết
                        context = _optimize_context(data)
                        break
                        
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    return config.ERROR_MESSAGES.get("connection_error", "Connection error: {error}").format(error=str(e))
                await asyncio.sleep(retry_delay * (attempt + 1))
        
        # Khởi tạo LLM
        llm = ChatGoogleGenerativeAI(
            model=config.DEFAULT_MODEL_NAME,
            temperature=config.DEFAULT_TEMPERATURE,
            google_api_key=config.GOOGLE_API_KEY
        )
        
        # Tạo prompt template với cấu trúc rõ ràng hơn và bao gồm lịch sử trò chuyện
        api_qa_prompt = ChatPromptTemplate.from_template(config.API_CHAT_PROMPT_TEMPLATE)
        
        # Chuẩn bị lịch sử trò chuyện nếu có
        chat_history_text = ""
        if chat_history and len(chat_history) > 0:
            chat_history_text = "Lịch sử trò chuyện:\n"
            for msg in chat_history:
                role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                chat_history_text += f"{role}: {msg['content']}\n"
        
        # Tạo chuỗi xử lý tối ưu
        api_qa_chain = (
            {
                "context": lambda x: x["context"], 
                "question": lambda x: x["question"],
                "chat_history_text": lambda x: x["chat_history_text"]
            }
            | api_qa_prompt
            | llm
            | StrOutputParser()
        )
        
        # Tạo phản hồi với timeout
        try:
            response = await asyncio.wait_for(
                api_qa_chain.ainvoke({
                    "context": context,
                    "question": answer,
                    "chat_history_text": chat_history_text
                }),
                timeout=60
            )
            return response
        except asyncio.TimeoutError:
            return config.ERROR_MESSAGES.get("timeout_error", "Request timed out")
        
    except Exception as e:
        logger.error(f"Error generating response from API: {str(e)}")
        return config.ERROR_MESSAGES.get("processing_error", "Processing error: {error}").format(error=str(e))

def _optimize_context(data: Dict[str, Any]) -> str:
    """Tối ưu hóa context bằng cách lọc và định dạng dữ liệu.
    
    Tham số:
        data: Dữ liệu JSON từ API
        
    Trả về:
        Chuỗi context đã được tối ưu
    """
    # Loại bỏ các trường không cần thiết
    if isinstance(data, dict):
        filtered_data = {
            k: v for k, v in data.items() 
            if not k.startswith('_') and v is not None
        }
    else:
        filtered_data = data
        
    # Chuyển đổi thành chuỗi với định dạng đẹp
    return json.dumps(filtered_data, ensure_ascii=False, indent=2)
