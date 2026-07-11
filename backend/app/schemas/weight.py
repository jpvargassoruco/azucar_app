from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class WeightBase(BaseModel):
    datetime: datetime
    weight_kg: float = Field(..., gt=0, lte=300, description="Weight in kilograms")
    notes: Optional[str] = None

class WeightCreate(WeightBase):
    pass

class WeightResponse(WeightBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
