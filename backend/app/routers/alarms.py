from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.models.alarm import Alarm
from app.models.user import User
from app.schemas.alarm import AlarmCreate, AlarmUpdate, AlarmResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AlarmResponse])
async def get_alarms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all alarms defined by the current user."""
    result = await db.execute(
        select(Alarm)
        .filter(Alarm.user_id == current_user.id)
        .order_by(Alarm.config_time.asc())
    )
    return result.scalars().all()

@router.post("/", response_model=AlarmResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_alarm(
    alarm_in: AlarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alarm, or update it if an alarm of the same type already exists."""
    result = await db.execute(
        select(Alarm)
        .filter(Alarm.user_id == current_user.id, Alarm.type == alarm_in.type)
    )
    db_alarm = result.scalars().first()
    
    if db_alarm:
        db_alarm.config_time = alarm_in.config_time
        db_alarm.is_active = alarm_in.is_active
    else:
        db_alarm = Alarm(
            user_id=current_user.id,
            type=alarm_in.type,
            config_time=alarm_in.config_time,
            is_active=alarm_in.is_active
        )
        db.add(db_alarm)
        
    await db.commit()
    await db.refresh(db_alarm)
    return db_alarm

@router.put("/{alarm_id}", response_model=AlarmResponse)
async def update_alarm(
    alarm_id: int,
    alarm_update: AlarmUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify the parameters (e.g. active toggle or time setting) of an alarm."""
    result = await db.execute(
        select(Alarm)
        .filter(Alarm.id == alarm_id, Alarm.user_id == current_user.id)
    )
    db_alarm = result.scalars().first()
    if not db_alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarma no encontrada."
        )
        
    if alarm_update.config_time is not None:
        db_alarm.config_time = alarm_update.config_time
    if alarm_update.is_active is not None:
        db_alarm.is_active = alarm_update.is_active
        
    await db.commit()
    await db.refresh(db_alarm)
    return db_alarm

@router.delete("/{alarm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific reminder alarm."""
    result = await db.execute(
        select(Alarm)
        .filter(Alarm.id == alarm_id, Alarm.user_id == current_user.id)
    )
    db_alarm = result.scalars().first()
    if not db_alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarma no encontrada."
        )
    await db.delete(db_alarm)
    await db.commit()
