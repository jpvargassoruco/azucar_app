from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.models.hba1c import HbA1c
from app.models.user import User
from app.schemas.hba1c import HbA1cCreate, HbA1cResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[HbA1cResponse])
async def get_hba1c_readings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all HbA1c readings for the current user."""
    result = await db.execute(
        select(HbA1c)
        .filter(HbA1c.user_id == current_user.id)
        .order_by(HbA1c.datetime.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=HbA1cResponse, status_code=status.HTTP_201_CREATED)
async def create_hba1c_reading(
    hba1c_in: HbA1cCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new HbA1c lab reading."""
    db_hba1c = HbA1c(
        user_id=current_user.id,
        datetime=hba1c_in.datetime,
        value_percent=hba1c_in.value_percent,
        notes=hba1c_in.notes
    )
    db.add(db_hba1c)
    await db.commit()
    await db.refresh(db_hba1c)
    return db_hba1c

@router.delete("/{hba1c_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hba1c_reading(
    hba1c_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific HbA1c reading."""
    result = await db.execute(
        select(HbA1c)
        .filter(HbA1c.id == hba1c_id, HbA1c.user_id == current_user.id)
    )
    db_hba1c = result.scalars().first()
    if not db_hba1c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HbA1c reading not found")
    db.delete(db_hba1c)
    await db.commit()
