from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[dict] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: Optional[str] = None