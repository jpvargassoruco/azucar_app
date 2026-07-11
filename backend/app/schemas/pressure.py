from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PressureBase(BaseModel):
    datetime: datetime
    systolic_mmhg: int = Field(..., ge=40, le=250, description="Systolic pressure in mmHg")
    diastolic_mmhg: int = Field(..., ge=40, le=250, description="Diastolic pressure in mmHg")
    notes: Optional[str] = None

class PressureCreate(PressureBase):
    pass

class PressureResponse(PressureBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
