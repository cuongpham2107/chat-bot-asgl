import logging
from typing import List, Dict, Any, Optional

from .chat_agent import ChatAgent
from .config import ChatAgentConfig as config

# Cấu hình logging
logger = logging.getLogger(__name__)

# Instance singleton của agent chat được tải lười biếng
_default_agent = None

async def get_default_agent() -> ChatAgent:
    """Lấy hoặc tạo agent chat mặc định."""
    global _default_agent
    if _default_agent is None:
        _default_agent = ChatAgent()
    return _default_agent

async def generate_chat_response(message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Tạo phản hồi cho tin nhắn của người dùng sử dụng agent mặc định.
    
    Tham số:
        message: Tin nhắn của người dùng.
        chat_history: Danh sách tùy chọn các tin nhắn trước đó theo định dạng 
                     [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Trả về:
        Phản hồi của trợ lý AI.
    """
    try:
        agent = await get_default_agent()
        return await agent.generate_response(message, chat_history)
    except Exception as e:
        logger.error(f"Error in generate_chat_response: {str(e)}")
        return config.ERROR_MESSAGES["processing_error"].format(error=str(e))

async def generate_chat_title(message: str) -> str:
    """Tạo tiêu đề cho cuộc trò chuyện dựa trên tin nhắn đầu tiên của người dùng.
    
    Tham số:
        message: Tin nhắn đầu tiên của người dùng.
        
    Trả về:
        Tiêu đề ngắn gọn cho cuộc trò chuyện.
    """
    try:
        agent = await get_default_agent()
        return await agent.generate_title(message)
    except Exception as e:
        logger.error(f"Error in generate_chat_title: {str(e)}")
        return config.DEFAULT_CHAT_TITLE

async def create_custom_agent(
    model_name: str = config.DEFAULT_MODEL_NAME, 
    temperature: float = config.DEFAULT_TEMPERATURE,
    system_prompt: str = config.DEFAULT_SYSTEM_PROMPT,
    api_key: Optional[str] = None
) -> ChatAgent:
    """Tạo một agent chat tùy chỉnh với các tham số cụ thể.
    
    Tham số:
        model_name: Tên của mô hình Google Generative AI sử dụng.
        temperature: Điều khiển tính ngẫu nhiên trong đầu ra.
        system_prompt: Prompt hệ thống sử dụng cho cuộc trò chuyện.
        api_key: Google API key. Nếu None, sẽ sử dụng GOOGLE_API_KEY từ biến môi trường.
    
    Trả về:
        Một instance ChatAgent mới.
    """
    return ChatAgent(model_name=model_name, temperature=temperature, system_prompt=system_prompt, api_key=api_key)

async def generate_response_with_custom_agent(
    agent: ChatAgent, 
    message: str, 
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Tạo phản hồi sử dụng một agent tùy chỉnh.
    
    Tham số:
        agent: Instance ChatAgent sử dụng.
        message: Tin nhắn của người dùng.
        chat_history: Danh sách tùy chọn các tin nhắn trước đó.
    
    Trả về:
        Phản hồi của trợ lý AI.
    """
    return await agent.generate_response(message, chat_history)
