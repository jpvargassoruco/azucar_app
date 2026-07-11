from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe incluir al menos una letra mayúscula.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe incluir al menos una letra minúscula.")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe incluir al menos un dígito.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=;:\[\]]", v):
            raise ValueError("La contraseña debe incluir al menos un carácter especial (!@#$%^&*...).")
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    has_ai_key: bool = False
    ai_api_key_masked: Optional[str] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True

class UserUpdateAI(BaseModel):
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    height: Optional[int] = None

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
