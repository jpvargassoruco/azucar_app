from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class MealPlanRequest(BaseModel):
    preferences: Optional[str] = None
    num_meals: int = 3

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    preferences: Optional[str] = None
    plan_data: Dict[str, Any]

    class Config:
        from_attributes = True
