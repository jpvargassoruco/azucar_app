from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, datetime, timezone
from typing import List, Optional

from app.database import get_db
from app.models.medication import Medication, MedicationLog
from app.models.user import User
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationLogMark,
    MedicationLogResponse,
    DoseSlot,
)
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[MedicationResponse])
async def get_medications(
    kind: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all medications/supplements defined by the current user."""
    query = select(Medication).filter(Medication.user_id == current_user.id)
    if kind:
        query = query.filter(Medication.kind == kind)
    result = await db.execute(query.order_by(Medication.name.asc()))
    return result.scalars().all()

@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    medication_in: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new medication or supplement entry."""
    db_medication = Medication(
        user_id=current_user.id,
        **medication_in.model_dump()
    )
    db.add(db_medication)
    await db.commit()
    await db.refresh(db_medication)
    return db_medication

@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: int,
    medication_update: MedicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify the parameters of an existing medication/supplement."""
    result = await db.execute(
        select(Medication)
        .filter(Medication.id == medication_id, Medication.user_id == current_user.id)
    )
    db_medication = result.scalars().first()
    if not db_medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado."
        )

    for field, value in medication_update.model_dump(exclude_unset=True).items():
        setattr(db_medication, field, value)

    await db.commit()
    await db.refresh(db_medication)
    return db_medication

@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    medication_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific medication or supplement."""
    result = await db.execute(
        select(Medication)
        .filter(Medication.id == medication_id, Medication.user_id == current_user.id)
    )
    db_medication = result.scalars().first()
    if not db_medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado."
        )
    await db.delete(db_medication)
    await db.commit()

@router.get("/today", response_model=List[DoseSlot])
async def get_today_doses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compute today's dose slots for all active medications, with their taken/skipped status."""
    today = date.today()
    weekday = today.weekday()

    result = await db.execute(
        select(Medication)
        .filter(Medication.user_id == current_user.id, Medication.is_active == True)
    )
    medications = result.scalars().all()

    log_result = await db.execute(
        select(MedicationLog)
        .filter(MedicationLog.user_id == current_user.id, MedicationLog.date == today)
    )
    logs_by_key = {
        (log.medication_id, log.scheduled_time): log
        for log in log_result.scalars().all()
    }

    slots: List[DoseSlot] = []
    for med in medications:
        if weekday not in med.days_of_week:
            continue
        for t in med.times:
            log = logs_by_key.get((med.id, t))
            slots.append(DoseSlot(
                medication_id=med.id,
                name=med.name,
                kind=med.kind,
                dosage=med.dosage,
                scheduled_time=t,
                status=log.status if log else None,
                log_id=log.id if log else None
            ))

    slots.sort(key=lambda s: s.scheduled_time)
    return slots

@router.post("/log", response_model=MedicationLogResponse)
async def mark_dose(
    log_in: MedicationLogMark,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a scheduled dose as taken or skipped (upsert by medication/date/time)."""
    med_result = await db.execute(
        select(Medication)
        .filter(Medication.id == log_in.medication_id, Medication.user_id == current_user.id)
    )
    if not med_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento no encontrado."
        )

    result = await db.execute(
        select(MedicationLog)
        .filter(
            MedicationLog.medication_id == log_in.medication_id,
            MedicationLog.date == log_in.date,
            MedicationLog.scheduled_time == log_in.scheduled_time
        )
    )
    db_log = result.scalars().first()

    if db_log:
        db_log.status = log_in.status
        db_log.marked_at = datetime.now(timezone.utc)
    else:
        db_log = MedicationLog(
            medication_id=log_in.medication_id,
            user_id=current_user.id,
            date=log_in.date,
            scheduled_time=log_in.scheduled_time,
            status=log_in.status
        )
        db.add(db_log)

    await db.commit()
    await db.refresh(db_log)
    return db_log
