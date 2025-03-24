from fastapi import APIRouter, Body, File, HTTPException, Depends, BackgroundTasks, UploadFile, logger
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.models.chat import DocumentChatRequest, DocumentChatResponse
from ..models.message import ApiChatRequest, MessageCreate, MessageResponse, MessageUpdate
from prisma.models import Message, User
from ..database import prisma
from ..utils.auth import get_current_user
from ..core.agents import chat_with_document, generate_chat_response, format_chat_history, generate_chat_title, generate_response_from_api

router = APIRouter()


@router.post("/", response_model=MessageResponse)
async def create_message(message: MessageCreate, current_user: User = Depends(get_current_user)):
    """
    Tạo một tin nhắn mới trong cuộc trò chuyện.
    
    API này cho phép người dùng tạo một tin nhắn mới trong cuộc trò chuyện mà họ sở hữu.
    Tin nhắn có thể có vai trò là "user" hoặc "assistant".
    
    Tham số:
        message: Dữ liệu tin nhắn cần tạo (bao gồm role, content, chatId)
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn đã được tạo
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện
        403: Nếu người dùng không có quyền thêm tin nhắn vào cuộc trò chuyện này
    """
    # Check if chat exists
    chat = await prisma.chat.find_unique(where={"id": message.chatId})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add messages to this chat")
    
    # Create the message
    new_message = await prisma.message.create(
        data={
            "role": message.role,
            "content": message.content,
            "chatId": message.chatId,
        }
    )
    return new_message


class UnifiedChatRequest(BaseModel):
    """Request model for unified chat API."""
    content: str
    source_file_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/chat/{chat_id}/send", response_model=MessageResponse)
async def send_message_and_get_response(
    chat_id: str, 
    request: UnifiedChatRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Gửi tin nhắn và nhận phản hồi từ AI (hỗ trợ cả chat thường và chat với tài liệu).
    
    API này cho phép người dùng gửi tin nhắn và nhận phản hồi tự động từ AI.
    Hỗ trợ cả hai chế độ:
    - Chat thường: Chỉ cần cung cấp nội dung tin nhắn (content)
    - Chat với tài liệu: Cung cấp nội dung tin nhắn (content), ID tài liệu (source_file_id) và metadata tùy chọn
    
    Quy trình hoạt động:
    1. Lưu tin nhắn của người dùng vào cơ sở dữ liệu
    2. Lấy lịch sử trò chuyện
    3. Tạo phản hồi AI dựa trên tin nhắn và lịch sử (với hoặc không với tài liệu)
    4. Lưu phản hồi AI vào cơ sở dữ liệu
    5. Tạo tiêu đề tự động nếu đây là tin nhắn đầu tiên
    
    Tham số:
        chat_id: ID của cuộc trò chuyện
        request: Dữ liệu tin nhắn (content, source_file_id tùy chọn, metadata tùy chọn)
        background_tasks: Đối tượng quản lý tác vụ nền (tùy chọn)
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn phản hồi từ AI
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện
        403: Nếu người dùng không có quyền thêm tin nhắn vào cuộc trò chuyện này
        500: Nếu có lỗi xảy ra trong quá trình xử lý
    """
    try:
        # Check if chat exists
        chat = await prisma.chat.find_unique(where={"id": chat_id})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Check if the user owns this chat
        if chat.userId != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to add messages to this chat")
        
        # Create the user message
        user_message = await prisma.message.create(
            data={
                "role": "user",
                "content": request.content,
                "chatId": chat_id,
            }
        )
        
        # Get chat history
        chat_history = await prisma.message.find_many(
            where={"chatId": chat_id},
            order={"createdAt": "asc"}
        )
        
        # Format chat history for the AI
        formatted_history = await format_chat_history(chat_history)
        
        # Generate AI response based on request type
        if request.source_file_id:
            # Document chat mode
            ai_response = await chat_with_document(
                message=request.content,
                source_file_id=request.source_file_id,
                metadata=request.metadata,
                chat_history=formatted_history
            )
        else:
            # Regular chat mode
            ai_response = await generate_chat_response(request.content, formatted_history)
        
        # Create the AI message
        ai_message = await prisma.message.create(
            data={
                "role": "assistant",
                "content": ai_response,
                "chatId": chat_id,
            }
        )
        
        # Nếu đây là tin nhắn đầu tiên trong trò chuyện và tiêu đề là mặc định, hãy tạo một tiêu đề mới
        if len(chat_history) <= 2 and (chat.title == "Cuộc trò chuyện mới" or chat.title == "New chat"):
            # Generate a title based on the user's message
            new_title = await generate_chat_title(request.content)
            
            # Update the chat title
            await prisma.chat.update(
                where={"id": chat_id},
                data={"title": new_title}
            )
        
        return ai_message
        
    except Exception as e:
        logger.error(f"Error in unified chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {str(e)}"
        )

# For backward compatibility with regular chat
@router.post("/chat/{chat_id}/message", response_model=MessageResponse)
async def send_regular_message(
    chat_id: str,
    request: MessageCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Gửi tin nhắn thông thường (endpoint cũ giữ lại để tương thích ngược).
    
    Tham số:
    - content: Nội dung tin nhắn
    
    Trả lại:
    - Đối tượng tin nhắn phản hồi từ AI
    """
    # Convert MessageCreate to UnifiedChatRequest
    unified_request = UnifiedChatRequest(
        content=request.content
    )
    
    # Call the unified endpoint
    return await send_message_and_get_response(
        chat_id=chat_id,
        request=unified_request,
        current_user=current_user
    )


# Send message with link api data and answer


@router.get("/chat/{chat_id}", response_model=list[MessageResponse])
async def get_chat_messages(chat_id: str, current_user: User = Depends(get_current_user)):
    """
    Lấy tất cả tin nhắn trong một cuộc trò chuyện.
    
    API này trả về danh sách tất cả tin nhắn trong một cuộc trò chuyện cụ thể.
    Người dùng có thể xem tin nhắn trong cuộc trò chuyện của họ hoặc trong cuộc trò chuyện công khai.
    
    Tham số:
        chat_id: ID của cuộc trò chuyện
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Danh sách các đối tượng tin nhắn, sắp xếp theo thời gian tạo
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện
        403: Nếu người dùng không có quyền xem tin nhắn trong cuộc trò chuyện này
    """
    # Check if chat exists
    chat = await prisma.chat.find_unique(where={"id": chat_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat or if it's public
    if chat.userId != current_user.id and chat.visibility != "public":
        raise HTTPException(status_code=403, detail="Not authorized to view messages in this chat")
    
    # Get all messages for the chat
    messages = await prisma.message.find_many(
        where={"chatId": chat_id},
        order={"createdAt": "asc"}
    )
    return messages

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str, current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin chi tiết của một tin nhắn cụ thể.
    
    API này trả về thông tin chi tiết của một tin nhắn dựa trên ID.
    Người dùng có thể xem tin nhắn trong cuộc trò chuyện của họ hoặc trong cuộc trò chuyện công khai.
    
    Tham số:
        message_id: ID của tin nhắn
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn
        
    Raises:
        404: Nếu không tìm thấy tin nhắn
        403: Nếu người dùng không có quyền xem tin nhắn này
    """
    # Get the message
    message = await prisma.message.find_unique(
        where={"id": message_id},
        include={"chat": True}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if the user owns the chat containing this message or if it's public
    if message.chat.userId != current_user.id and message.chat.visibility != "public":
        raise HTTPException(status_code=403, detail="Not authorized to view this message")
    
    return message

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(message_id: str, message_data: MessageUpdate, current_user: User = Depends(get_current_user)):
    """
    Cập nhật nội dung của một tin nhắn.
    
    API này cho phép người dùng cập nhật nội dung hoặc vai trò của một tin nhắn trong cuộc trò chuyện của họ.
    
    Tham số:
        message_id: ID của tin nhắn cần cập nhật
        message_data: Dữ liệu cập nhật (có thể bao gồm role và/hoặc content)
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn đã được cập nhật
        
    Raises:
        404: Nếu không tìm thấy tin nhắn
        403: Nếu người dùng không có quyền cập nhật tin nhắn này
    """
    # Get the message with its chat
    message = await prisma.message.find_unique(
        where={"id": message_id},
        include={"chat": True}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if the user owns the chat containing this message
    if message.chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this message")
    
    # Prepare update data
    update_data = message_data.dict(exclude_unset=True)
    
    # Update the message
    updated_message = await prisma.message.update(
        where={"id": message_id},
        data=update_data
    )
    return updated_message

@router.post("/chat/{chat_id}/generate-title", response_model=dict)
async def generate_title_for_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Tạo hoặc tạo lại tiêu đề cho cuộc trò chuyện dựa trên tin nhắn đầu tiên của người dùng.
    
    API này sử dụng AI để tạo một tiêu đề ngắn gọn và mô tả cho cuộc trò chuyện
    dựa trên nội dung của tin nhắn đầu tiên từ người dùng.
    
    Tham số:
        chat_id: ID của cuộc trò chuyện
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng chứa ID và tiêu đề mới của cuộc trò chuyện
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện
        403: Nếu người dùng không có quyền cập nhật cuộc trò chuyện này
        400: Nếu không tìm thấy tin nhắn người dùng nào trong cuộc trò chuyện
    """
    # Check if chat exists
    chat = await prisma.chat.find_unique(where={"id": chat_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this chat")
    
    # Get the first user message
    first_message = await prisma.message.find_first(
        where={
            "chatId": chat_id,
            "role": "user"
        },
        order={"createdAt": "asc"}
    )
    
    if not first_message:
        raise HTTPException(status_code=400, detail="No user messages found in this chat")
    
    # Generate a title based on the first message
    new_title = await generate_chat_title(first_message.content)
    
    # Update the chat title
    updated_chat = await prisma.chat.update(
        where={"id": chat_id},
        data={"title": new_title}
    )
    
    return {"id": updated_chat.id, "title": updated_chat.title}

@router.delete("/{message_id}", response_model=MessageResponse)
async def delete_message(message_id: str, current_user: User = Depends(get_current_user)):
    """
    Xóa một tin nhắn.
    
    API này cho phép người dùng xóa một tin nhắn trong cuộc trò chuyện của họ.
    
    Tham số:
        message_id: ID của tin nhắn cần xóa
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn đã bị xóa
        
    Raises:
        404: Nếu không tìm thấy tin nhắn
        403: Nếu người dùng không có quyền xóa tin nhắn này
    """
    # Get the message with its chat
    message = await prisma.message.find_unique(
        where={"id": message_id},
        include={"chat": True}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if the user owns the chat containing this message
    if message.chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    # Delete the message
    deleted_message = await prisma.message.delete(where={"id": message_id})
    return deleted_message

@router.post("/chat/{chat_id}/regenerate/{message_id}", response_model=MessageResponse)
async def regenerate_ai_response(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Tạo lại phản hồi AI cho một tin nhắn cụ thể.
    
    API này cho phép người dùng tạo lại phản hồi AI cho một tin nhắn cụ thể.
    Hữu ích khi người dùng muốn có một phản hồi khác từ AI cho cùng một câu hỏi.
    
    Quy trình hoạt động:
    1. Lấy lịch sử trò chuyện đến thời điểm của tin nhắn cần tạo lại
    2. Tìm tin nhắn người dùng gần nhất trước đó
    3. Tạo phản hồi AI mới dựa trên tin nhắn người dùng và lịch sử
    4. Cập nhật tin nhắn AI hiện tại với nội dung mới
    
    Tham số:
        chat_id: ID của cuộc trò chuyện
        message_id: ID của tin nhắn AI cần tạo lại
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn AI đã được cập nhật với nội dung mới
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện hoặc tin nhắn
        403: Nếu người dùng không có quyền tạo lại tin nhắn trong cuộc trò chuyện này
        400: Nếu tin nhắn không phải là tin nhắn AI hoặc không tìm thấy tin nhắn người dùng trước đó
    """
    # Check if chat exists
    chat = await prisma.chat.find_unique(where={"id": chat_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to regenerate messages in this chat")
    
    # Get the message to regenerate
    message = await prisma.message.find_unique(
        where={"id": message_id},
        include={"chat": True}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if the message is an AI message
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="Can only regenerate AI responses")
    
    # Get chat history up to this message
    chat_history = await prisma.message.find_many(
        where={
            "chatId": chat_id,
            "createdAt": {"lt": message.createdAt}
        },
        order={"createdAt": "asc"}
    )
    
    # Get the last user message
    last_user_message = None
    for msg in reversed(chat_history):
        if msg.role == "user":
            last_user_message = msg
            break
    
    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found to respond to")
    
    # Format chat history for the AI
    formatted_history = await format_chat_history(chat_history)
    
    # Generate new AI response
    new_ai_response = await generate_chat_response(last_user_message.content, formatted_history)
    
    # Update the AI message
    updated_message = await prisma.message.update(
        where={"id": message_id},
        data={"content": new_ai_response}
    )
    
    return updated_message


@router.post("/{chat_id}/api-chat", response_model=MessageResponse)
async def chat_with_api(
    chat_id: str,
    request: ApiChatRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Gửi tin nhắn và nhận phản hồi từ AI dựa trên dữ liệu từ API bên ngoài.
    
    API này cho phép người dùng gửi tin nhắn và nhận phản hồi từ AI dựa trên dữ liệu
    được lấy từ một API bên ngoài.
    
    Quy trình hoạt động:
    1. Kiểm tra quyền truy cập chat
    2. Lưu tin nhắn của người dùng
    3. Lấy dữ liệu từ API bên ngoài
    4. Tạo phản hồi AI dựa trên dữ liệu API
    5. Lưu phản hồi AI
    
    Tham số:
        chat_id: ID của cuộc trò chuyện
        request: Dữ liệu tin nhắn (content, api_url)
        current_user: Người dùng hiện tại (được xác thực qua token JWT)
    
    Trả về:
        Đối tượng tin nhắn phản hồi từ AI
        
    Raises:
        404: Nếu không tìm thấy cuộc trò chuyện
        403: Nếu người dùng không có quyền thêm tin nhắn vào cuộc trò chuyện này
        500: Nếu có lỗi xảy ra trong quá trình xử lý
    """
    try:
        # Kiểm tra chat tồn tại
        chat = await prisma.chat.find_unique(where={"id": chat_id})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Kiểm tra quyền truy cập
        if chat.userId != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to add messages to this chat")
        
        # Tạo tin nhắn của người dùng
        user_message = await prisma.message.create(
            data={
                "role": "user",
                "content": request.content,
                "chatId": chat_id,
            }
        )
        
        # Lấy lịch sử trò chuyện
        chat_history = await prisma.message.find_many(
            where={"chatId": chat_id},
            order={"createdAt": "asc"}
        )
        
        # Format lịch sử trò chuyện
        formatted_history = await format_chat_history(chat_history)
        
        # Tạo phản hồi AI dựa trên dữ liệu API
        ai_response = await generate_response_from_api(
            answer=request.content,
            url_api=request.api_url,
            chat_history=formatted_history
        )
        
        # Tạo tin nhắn AI
        ai_message = await prisma.message.create(
            data={
                "role": "assistant",
                "content": ai_response,
                "chatId": chat_id,
            }
        )
        
        # Nếu đây là tin nhắn đầu tiên và tiêu đề là mặc định, tạo tiêu đề mới
        if len(chat_history) <= 2 and (chat.title == "Cuộc trò chuyện mới" or chat.title == "New chat"):
            new_title = await generate_chat_title(request.content)
            await prisma.chat.update(
                where={"id": chat_id},
                data={"title": new_title}
            )
        
        return ai_message
        
    except Exception as e:
        logger.error(f"Error in API chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process API chat: {str(e)}"
        )
