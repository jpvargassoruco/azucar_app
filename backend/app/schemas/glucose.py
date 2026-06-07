from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GlucoseReadingBase(BaseModel):
    datetime: datetime
    value_mgdl: int = Field(..., gt=0, lt=1000, description="Nivel de glucosa en mg/dL")
    condition: str = Field(..., description="Condición de la lectura: 'ayunas', 'postprandial', 'otro'")
    notes: Optional[str] = None

class GlucoseReadingCreate(GlucoseReadingBase):
    pass

class GlucoseReadingResponse(GlucoseReadingBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
