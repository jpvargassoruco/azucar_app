from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    has_ai_key: bool = False
    ai_api_key_masked: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdateAI(BaseModel):
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None

class AITestRequest(BaseModel):
    ai_provider: str
    ai_api_key: str
    ai_model: str
    ai_base_url: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None
