from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class AIAnalysisDetail(BaseModel):
    food_items: List[str]
    calories_estimated: int
    carbs_g: int
    protein_g: int
    fat_g: int
    fiber_g: int
    glycemic_impact: str  # "bajo", "moderado", "alto"
    recommendation: str

class MealEntryResponse(BaseModel):
    id: int
    user_id: int
    datetime: datetime
    photo_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    notes: Optional[str] = None
    ai_analysis: Optional[AIAnalysisDetail] = None

    class Config:
        from_attributes = True
