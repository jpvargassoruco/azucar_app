from sqlalchemy import ForeignKey, Date, DateTime, String, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from typing import List, Optional
from app.database import Base

class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # "medication" | "supplement"
    dosage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. "850mg", "1 cápsula"
    times: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # ["08:00", "20:00"]
    days_of_week: Mapped[List[int]] = mapped_column(JSON, nullable=False)  # [0..6], 0=lunes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="medications")

class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    medication_id: Mapped[int] = mapped_column(ForeignKey("medications.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # "taken" | "skipped"
    marked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("medication_id", "date", "scheduled_time", name="uq_medication_date_time"),
    )
