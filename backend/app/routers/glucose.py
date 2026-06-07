from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.glucose import GlucoseReading
from app.models.user import User
from app.schemas.glucose import GlucoseReadingCreate, GlucoseReadingResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[GlucoseReadingResponse])
async def get_glucose_readings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all glucose readings for the current user, ordered descending by datetime."""
    result = await db.execute(
        select(GlucoseReading)
        .filter(GlucoseReading.user_id == current_user.id)
        .order_by(GlucoseReading.datetime.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=GlucoseReadingResponse, status_code=status.HTTP_201_CREATED)
async def create_glucose_reading(
    reading_in: GlucoseReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new glucose reading for the authenticated user."""
    db_reading = GlucoseReading(
        user_id=current_user.id,
        datetime=reading_in.datetime,
        value_mgdl=reading_in.value_mgdl,
        condition=reading_in.condition,
        notes=reading_in.notes
    )
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading

@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_glucose_reading(
    reading_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific glucose reading."""
    result = await db.execute(
        select(GlucoseReading)
        .filter(GlucoseReading.id == reading_id, GlucoseReading.user_id == current_user.id)
    )
    db_reading = result.scalars().first()
    if not db_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lectura de glucosa no encontrada."
        )
    await db.delete(db_reading)
    await db.commit()

@router.get("/stats")
async def get_glucose_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate averages and totals of glucose readings for dashboard counters."""
    # Overall average
    avg_all_q = await db.execute(
        select(func.avg(GlucoseReading.value_mgdl))
        .filter(GlucoseReading.user_id == current_user.id)
    )
    avg_all = avg_all_q.scalar()
    
    # Fasting average
    avg_fasting_q = await db.execute(
        select(func.avg(GlucoseReading.value_mgdl))
        .filter(GlucoseReading.user_id == current_user.id, GlucoseReading.condition == "ayunas")
    )
    avg_fasting = avg_fasting_q.scalar()
    
    # Postprandial average
    avg_postprandial_q = await db.execute(
        select(func.avg(GlucoseReading.value_mgdl))
        .filter(GlucoseReading.user_id == current_user.id, GlucoseReading.condition == "postprandial")
    )
    avg_postprandial = avg_postprandial_q.scalar()
    
    # Total count
    count_q = await db.execute(
        select(func.count(GlucoseReading.id))
        .filter(GlucoseReading.user_id == current_user.id)
    )
    count = count_q.scalar()
    
    return {
        "avg_all": round(avg_all, 1) if avg_all is not None else 0,
        "avg_fasting": round(avg_fasting, 1) if avg_fasting is not None else 0,
        "avg_postprandial": round(avg_postprandial, 1) if avg_postprandial is not None else 0,
        "readings_count": count
    }
