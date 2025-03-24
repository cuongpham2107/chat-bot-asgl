from typing import List, Dict, Any

async def format_chat_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Định dạng tin nhắn từ cơ sở dữ liệu thành định dạng mà agent chat mong đợi.
    
    Tham số:
        messages: Danh sách các đối tượng tin nhắn từ cơ sở dữ liệu.
    
    Trả về:
        Lịch sử trò chuyện đã được định dạng.
    """
    formatted_history = []
    for msg in messages:
        formatted_history.append({
            "role": msg.role,
            "content": msg.content
        })
    return formatted_history
