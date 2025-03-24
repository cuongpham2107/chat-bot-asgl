import json
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime

class FileBase(BaseModel):
    filename: str
    filepath: str
    metadata: Optional[Dict[str, Any]] = None

class FileCreate(FileBase):
    pass

class FileResponse(FileBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    
    # Convert metadata from JSON string to dictionary
    @validator('metadata', pre=True)
    def parse_metadata(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return {}

    class Config:
        from_attributes = True
