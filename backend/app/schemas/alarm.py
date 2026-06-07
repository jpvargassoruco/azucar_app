from pydantic import BaseModel, Field
from typing import Optional

class AlarmBase(BaseModel):
    type: str = Field(..., description="Tipo de alarma: 'metformina', 'hidratacion', 'postprandial'")
    config_time: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$", description="Hora en formato HH:MM (24 horas)")
    is_active: bool = True

class AlarmCreate(AlarmBase):
    pass

class AlarmUpdate(BaseModel):
    config_time: Optional[str] = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    is_active: Optional[bool] = None

class AlarmResponse(AlarmBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
