from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FastingSessionBase(BaseModel):
    start_time: datetime
    protocol: str  # e.g., "16:8", "12:12", "18:6"

class FastingSessionCreate(FastingSessionBase):
    pass

class FastingSessionUpdate(BaseModel):
    end_time: datetime
    completed: bool = True

class FastingSessionResponse(FastingSessionBase):
    id: int
    user_id: int
    end_time: Optional[datetime] = None
    completed: bool

    class Config:
        from_attributes = True
