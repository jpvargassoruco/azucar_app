from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HbA1cBase(BaseModel):
    datetime: datetime
    value_percent: float = Field(..., ge=3, le=15, description="HbA1c value in %")
    notes: Optional[str] = None

class HbA1cCreate(HbA1cBase):
    pass

class HbA1cResponse(HbA1cBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
