from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Literal

TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

class MedicationBase(BaseModel):
    name: str = Field(..., max_length=100)
    kind: Literal["medication", "supplement"]
    dosage: Optional[str] = Field(None, max_length=50)
    times: List[str] = Field(..., description="Horas en formato HH:MM (24 horas)")
    days_of_week: List[int] = Field(..., description="Días activos, 0=lunes .. 6=domingo")
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=255)

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    kind: Optional[Literal["medication", "supplement"]] = None
    dosage: Optional[str] = Field(None, max_length=50)
    times: Optional[List[str]] = None
    days_of_week: Optional[List[int]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=255)

class MedicationResponse(MedicationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class MedicationLogMark(BaseModel):
    medication_id: int
    date: date
    scheduled_time: str = Field(..., pattern=TIME_PATTERN)
    status: Literal["taken", "skipped"]

class MedicationLogResponse(BaseModel):
    id: int
    medication_id: int
    user_id: int
    date: date
    scheduled_time: str
    status: str

    class Config:
        from_attributes = True

class DoseSlot(BaseModel):
    medication_id: int
    name: str
    kind: str
    dosage: Optional[str]
    scheduled_time: str
    status: Optional[Literal["taken", "skipped"]]
    log_id: Optional[int]
