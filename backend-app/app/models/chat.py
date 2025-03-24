from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime
from .message import MessageResponse

class ChatBase(BaseModel):
    title: str
    visibility: Optional[str] = None

class ChatCreate(ChatBase):
    userId: str

class NewConversationRequest(BaseModel):
    message: str

class ChatResponse(ChatBase):
    id: str
    userId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class ChatDetailResponse(ChatResponse):
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    visibility: Optional[str] = None



class DocumentChatRequest(BaseModel):
    """Request model for document chat API."""
    message: str
    source_file_id: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentChatResponse(BaseModel):
    """Response model for document chat API."""
    response: str