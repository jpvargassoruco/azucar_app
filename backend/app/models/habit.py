from sqlalchemy import ForeignKey, Date, String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from app.database import Base

class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    habit_key: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "ejercicio", "agua", "ayuno", "medicacion"
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="habit_logs")

    __table_args__ = (
        UniqueConstraint("user_id", "date", "habit_key", name="uq_user_date_habit"),
    )
