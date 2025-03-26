from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .file import FileResponse

class MessageBase(BaseModel):
    role: str  # e.g., "user", "assistant", "system"
    content: str
    chatId: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    files: Optional[List[FileResponse]] = []

    class Config:
        from_attributes = True

class SqlChatRequest(BaseModel):
    content: str
    value_db_connect: str

class MessageUpdate(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
