from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    glucose_readings: Mapped[List["GlucoseReading"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    fasting_sessions: Mapped[List["FastingSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    habit_logs: Mapped[List["HabitLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alarms: Mapped[List["Alarm"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meals: Mapped[List["MealEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_subscriptions: Mapped[List["PushSubscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
