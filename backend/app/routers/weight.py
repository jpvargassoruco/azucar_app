from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.models.weight import Weight
from app.models.user import User
from app.schemas.weight import WeightCreate, WeightResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[WeightResponse])
async def get_weights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all weight readings for the current user, ordered by datetime descending."""
    result = await db.execute(
        select(Weight)
        .filter(Weight.user_id == current_user.id)
        .order_by(Weight.datetime.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
async def create_weight(
    weight_in: WeightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new weight reading for the authenticated user."""
    db_weight = Weight(
        user_id=current_user.id,
        datetime=weight_in.datetime,
        weight_kg=weight_in.weight_kg,
        notes=weight_in.notes
    )
    db.add(db_weight)
    await db.commit()
    await db.refresh(db_weight)
    return db_weight

@router.delete("/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(
    weight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific weight reading."""
    result = await db.execute(
        select(Weight)
        .filter(Weight.id == weight_id, Weight.user_id == current_user.id)
    )
    db_weight = result.scalars().first()
    if not db_weight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight reading not found")
    db.delete(db_weight)
    await db.commit()
