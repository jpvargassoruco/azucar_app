from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.models.pressure import Pressure
from app.models.user import User
from app.schemas.pressure import PressureCreate, PressureResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[PressureResponse])
async def get_pressures(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all blood pressure readings for the current user."""
    result = await db.execute(
        select(Pressure)
        .filter(Pressure.user_id == current_user.id)
        .order_by(Pressure.datetime.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=PressureResponse, status_code=status.HTTP_201_CREATED)
async def create_pressure(
    pressure_in: PressureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new blood pressure reading."""
    db_pressure = Pressure(
        user_id=current_user.id,
        datetime=pressure_in.datetime,
        systolic_mmhg=pressure_in.systolic_mmhg,
        diastolic_mmhg=pressure_in.diastolic_mmhg,
        notes=pressure_in.notes
    )
    db.add(db_pressure)
    await db.commit()
    await db.refresh(db_pressure)
    return db_pressure

@router.delete("/{pressure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pressure(
    pressure_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific blood pressure reading."""
    result = await db.execute(
        select(Pressure)
        .filter(Pressure.id == pressure_id, Pressure.user_id == current_user.id)
    )
    db_pressure = result.scalars().first()
    if not db_pressure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pressure reading not found")
    await db.delete(db_pressure)
    await db.commit()
