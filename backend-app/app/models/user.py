from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
