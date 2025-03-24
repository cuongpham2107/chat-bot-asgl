from fastapi import APIRouter, HTTPException, Depends
from ..models.chat import ChatCreate, ChatResponse, ChatDetailResponse, ChatUpdate
from ..models.message import MessageCreate, MessageResponse
from prisma.models import Chat, User
from ..database import prisma
from ..utils.auth import get_current_user
from ..core.agents import generate_chat_response, generate_chat_title

router = APIRouter()

# Ghi chú: Đây là hàm tạo 1 cuộc trò chuyện mới với thông điệp đầu tiên và phản hồi AI. chưa tích hợp chat với file vào function này 
@router.post("/new-conversation", response_model=ChatDetailResponse)
async def create_new_conversation(
    message: str,
    current_user: User = Depends(get_current_user)
):
    """
   Tạo một cuộc trò chuyện mới với thông điệp đầu tiên và phản hồi AI.

 API này tạo ra một cuộc trò chuyện mới, lưu tin nhắn đầu tiên của người dùng,
 Tạo phản hồi AI và tạo tiêu đề tự động dựa trên nội dung tin nhắn.

 Dòng chảy quá trình:
 1. Tạo một cuộc trò chuyện mới với một tiêu đề tạm thời
 2. Lưu tin nhắn người dùng
 3. Tạo phản hồi AI
 4. Tạo tiêu đề dựa trên thông báo người dùng
 5. Cập nhật tiêu đề cuộc trò chuyện
 6. Trả lại cuộc trò chuyện hoàn chỉnh với các tin nhắn

 Tham số:
 Tin nhắn: Nội dung của tin nhắn đầu tiên của người dùng
 current_user: người dùng được xác thực hiện tại (thông qua mã thông báo JWT)

 Trả lại:
 Hoàn thành đối tượng cuộc trò chuyện với các tin nhắn

 Tăng:
 500: Nếu có lỗi trong việc tạo cuộc trò chuyện hoặc tin nhắn
    """
    try:
        # Create new conversation with temporary title
        new_chat = await prisma.chat.create(
            data={
                "title": "New conversation",
                "visibility": "private",
                "userId": current_user.id,
            }
        )
        
        # Save user message
        user_message = await prisma.message.create(
            data={
                "role": "user",
                "content": message,
                "chatId": new_chat.id,
            }
        )
        
        # Generate AI response
        ai_response = await generate_chat_response(message, [{"role": "user", "content": message}])
        
        # Save AI response
        ai_message = await prisma.message.create(
            data={
                "role": "assistant",
                "content": ai_response,
                "chatId": new_chat.id,
            }
        )
        
        # Generate title based on user message
        chat_title = await generate_chat_title(message)
        
        # Update conversation title
        updated_chat = await prisma.chat.update(
            where={"id": new_chat.id},
            data={"title": chat_title},
            include={"messages": True}
        )
        
        return updated_chat
        
    except Exception as e:
        # Log error and return error message
        import logging
        logging.error(f"Error creating new conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating new conversation: {str(e)}"
        )

@router.post("/", response_model=ChatResponse)
async def create_chat(chat: ChatCreate, current_user: User = Depends(get_current_user)):
    # Create the chat with the current user's ID
    new_chat = await prisma.chat.create(
        data={
            "title": chat.title,
            "visibility": chat.visibility,
            "userId": current_user.id,  # Use the authenticated user's ID
        }
    )
    return new_chat

@router.get("/", response_model=list[ChatResponse])
async def get_chats(current_user: User = Depends(get_current_user)):
    # Get all chats for the current user
    chats = await prisma.chat.find_many(
        where={"userId": current_user.id},
        order={"createdAt": "desc"},
    )
    return chats


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(chat_id: str, current_user: User = Depends(get_current_user)):
    # Get chat with messages
    chat = await prisma.chat.find_unique(
        where={"id": chat_id},
        include={"messages": True}
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if chat.userId != current_user.id:
        # Allow access to public chats
        if chat.visibility != "public":
            raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    
    return chat

@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(chat_id: str, chat_data: ChatUpdate, current_user: User = Depends(get_current_user)):
    # Check if chat exists
    existing_chat = await prisma.chat.find_unique(where={"id": chat_id})
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if existing_chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this chat")
    
    # Prepare update data
    update_data = chat_data.dict(exclude_unset=True)
    
    # Update the chat
    updated_chat = await prisma.chat.update(
        where={"id": chat_id},
        data=update_data
    )
    return updated_chat

@router.delete("/{chat_id}", response_model=ChatResponse)
async def delete_chat(chat_id: str, current_user: User = Depends(get_current_user)):
    # Check if chat exists
    existing_chat = await prisma.chat.find_unique(where={"id": chat_id})
    if not existing_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Check if the user owns this chat
    if existing_chat.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")
    
    try:
        # First, delete all messages associated with this chat
        await prisma.message.delete_many(where={"chatId": chat_id})
        
        # Then delete the chat itself
        deleted_chat = await prisma.chat.delete(where={"id": chat_id})
        return deleted_chat
    except Exception as e:
        # Log the error and return a more helpful error message
        import logging
        logging.error(f"Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat: {str(e)}"
        )
