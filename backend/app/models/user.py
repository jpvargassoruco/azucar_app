from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # User-specific AI configurations
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    glucose_readings: Mapped[List["GlucoseReading"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    fasting_sessions: Mapped[List["FastingSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    habit_logs: Mapped[List["HabitLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alarms: Mapped[List["Alarm"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meals: Mapped[List["MealEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_subscriptions: Mapped[List["PushSubscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def has_ai_key(self) -> bool:
        return bool(self.ai_api_key)

    @property
    def ai_api_key_masked(self) -> Optional[str]:
        if not self.ai_api_key:
            return None
        key = self.ai_api_key.strip()
        if len(key) <= 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"

