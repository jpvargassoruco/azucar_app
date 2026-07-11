from sqlalchemy import ForeignKey, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Pressure(Base):
    __tablename__ = "blood_pressures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    systolic_mmhg: Mapped[int] = mapped_column(Integer, nullable=False)  # mmHg
    diastolic_mmhg: Mapped[int] = mapped_column(Integer, nullable=False)  # mmHg
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="pressures")
