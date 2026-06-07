from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # JWT Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # Push Notifications
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_MAILTO: str = "mailto:jpvargassoruco@gmail.com"
    
    # AI / Hermes
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/auto"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    HERMES_API_KEY: str = ""
    HERMES_URL: str = "http://hermes:8642"
    
    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    THUMBNAIL_SIZE: int = 400

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
