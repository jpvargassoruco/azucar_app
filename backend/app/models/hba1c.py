from sqlalchemy import ForeignKey, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base

class HbA1c(Base):
    __tablename__ = "hba1c_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    value_percent: Mapped[float] = mapped_column(Float, nullable=False)  # %
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="hba1c_readings")
