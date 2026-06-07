from pydantic import BaseModel
from datetime import date

class HabitLogToggle(BaseModel):
    date: date
    habit_key: str  # e.g., "ejercicio", "agua", "ayuno", "medicacion"

class HabitLogResponse(BaseModel):
    id: int
    user_id: int
    date: date
    habit_key: str
    completed: bool

    class Config:
        from_attributes = True

class HabitProgressResponse(BaseModel):
    habit_key: str
    completed_days: int
    total_days: int
    percentage: float
