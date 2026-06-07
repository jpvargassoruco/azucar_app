from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, timedelta
from typing import List, Dict
from app.database import get_db
from app.models.habit import HabitLog
from app.models.user import User
from app.schemas.habit import HabitLogToggle, HabitLogResponse, HabitProgressResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/today", response_model=Dict[str, bool])
async def get_today_habits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve completion states for today's habits."""
    today = date.today()
    result = await db.execute(
        select(HabitLog)
        .filter(HabitLog.user_id == current_user.id, HabitLog.date == today)
    )
    logs = result.scalars().all()
    
    # Standard keys used in the client PWA
    habits = {
        "ejercicio": False,
        "agua": False,
        "ayuno": False,
        "medicacion": False
    }
    for log in logs:
        if log.habit_key in habits:
            habits[log.habit_key] = log.completed
            
    return habits

@router.post("/toggle", response_model=HabitLogResponse)
async def toggle_habit(
    toggle_in: HabitLogToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle the completion state of a specific habit for a given date."""
    result = await db.execute(
        select(HabitLog)
        .filter(
            HabitLog.user_id == current_user.id,
            HabitLog.date == toggle_in.date,
            HabitLog.habit_key == toggle_in.habit_key
        )
    )
    db_log = result.scalars().first()
    
    if db_log:
        db_log.completed = not db_log.completed
    else:
        db_log = HabitLog(
            user_id=current_user.id,
            date=toggle_in.date,
            habit_key=toggle_in.habit_key,
            completed=True
        )
        db.add(db_log)
        
    await db.commit()
    await db.refresh(db_log)
    return db_log

@router.get("/progress", response_model=List[HabitProgressResponse])
async def get_habits_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate the completion percentage of habits over the last 30 days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=29)
    
    result = await db.execute(
        select(HabitLog)
        .filter(
            HabitLog.user_id == current_user.id,
            HabitLog.date >= start_date,
            HabitLog.date <= end_date,
            HabitLog.completed == True
        )
    )
    completed_logs = result.scalars().all()
    
    counts = {
        "ejercicio": 0,
        "agua": 0,
        "ayuno": 0,
        "medicacion": 0
    }
    for log in completed_logs:
        if log.habit_key in counts:
            counts[log.habit_key] += 1
            
    progress = []
    for key, count in counts.items():
        percentage = round((count / 30.0) * 100, 1)
        progress.append(
            HabitProgressResponse(
                habit_key=key,
                completed_days=count,
                total_days=30,
                percentage=percentage
            )
        )
    return progress
