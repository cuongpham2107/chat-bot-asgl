import logging
from typing import List, Dict, Any, Optional

from .default_agent import get_default_agent
from .config import ChatAgentConfig as config

# Cấu hình logging
logger = logging.getLogger(__name__)

async def embed_and_store_document(text: str, source_file_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Nhúng văn bản và lưu trữ trong ChromaDB sử dụng agent mặc định.
    
    Tham số:
        text: Nội dung văn bản cần nhúng.
        source_file_id: ID của file nguồn.
        metadata: Metadata bổ sung cho tài liệu.
        
    Trả về:
        ID của collection đã tạo trong ChromaDB.
    """
    try:
        agent = await get_default_agent()
        return await agent.embed_and_store_document(text, source_file_id, metadata)
    except Exception as e:
        logger.error(f"Error in embed_and_store_document: {str(e)}")
        raise

async def chat_with_document(message: str, source_file_id: str, metadata: Optional[Dict[str, Any]] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Trò chuyện với tài liệu đã được nhúng sử dụng agent mặc định.
    
    Tham số:
        message: Tin nhắn của người dùng.
        source_file_id: ID của file nguồn.
        metadata: Metadata của file, có thể chứa collection_id.
        chat_history: Danh sách tùy chọn các tin nhắn trước đó.
        
    Trả về:
        Phản hồi của trợ lý AI dựa trên tài liệu.
    """
    try:
        agent = await get_default_agent()
        return await agent.chat_with_document(message, source_file_id, metadata, chat_history)
    except Exception as e:
        logger.error(f"Error in chat_with_document: {str(e)}")
        return config.ERROR_MESSAGES["processing_error"].format(error=str(e))
