from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.glucose import GlucoseReading
from app.models.meal import MealEntry
from app.models.fasting import FastingSession
from app.auth.dependencies import get_current_user
from app.services.fhir_serializer import (
    user_to_patient,
    glucose_to_observation,
    meal_to_nutrition_intake,
    build_patient_bundle
)

router = APIRouter()

@router.get("/Patient", response_model=None)
async def get_patient(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user as a FHIR Patient resource."""
    patient = user_to_patient(current_user)
    return patient.dict(exclude_none=True)

@router.get("/Observation", response_model=None)
async def get_observations(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns glucose readings as FHIR Observations."""
    if category and category != "laboratory":
        return []
        
    result = await db.execute(
        select(GlucoseReading)
        .filter(GlucoseReading.user_id == current_user.id)
        .order_by(GlucoseReading.datetime.desc())
        .limit(100)
    )
    readings = result.scalars().all()
    
    patient_ref = f"Patient/{current_user.id}"
    observations = [glucose_to_observation(r, patient_ref).dict(exclude_none=True) for r in readings]
    return observations

@router.get("/NutritionIntake", response_model=None)
async def get_nutrition_intakes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns meals as FHIR NutritionIntake resources."""
    result = await db.execute(
        select(MealEntry)
        .filter(MealEntry.user_id == current_user.id)
        .order_by(MealEntry.datetime.desc())
        .limit(100)
    )
    meals = result.scalars().all()
    
    patient_ref = f"Patient/{current_user.id}"
    intakes = [meal_to_nutrition_intake(m, patient_ref).dict(exclude_none=True) for m in meals]
    return intakes

@router.get("/Bundle", response_model=None)
async def get_bundle(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns a complete FHIR Bundle with all patient data."""
    # Fetch data
    g_res = await db.execute(select(GlucoseReading).filter(GlucoseReading.user_id == current_user.id))
    readings = g_res.scalars().all()
    
    m_res = await db.execute(select(MealEntry).filter(MealEntry.user_id == current_user.id))
    meals = m_res.scalars().all()
    
    f_res = await db.execute(select(FastingSession).filter(FastingSession.user_id == current_user.id))
    fastings = f_res.scalars().all()
    
    bundle = build_patient_bundle(current_user, readings, meals, fastings)
    return bundle.dict(exclude_none=True)

@router.get("/Bundle/export", response_class=Response)
async def export_bundle(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Downloads the FHIR Bundle as a .json file."""
    # Fetch data
    g_res = await db.execute(select(GlucoseReading).filter(GlucoseReading.user_id == current_user.id))
    readings = g_res.scalars().all()
    
    m_res = await db.execute(select(MealEntry).filter(MealEntry.user_id == current_user.id))
    meals = m_res.scalars().all()
    
    f_res = await db.execute(select(FastingSession).filter(FastingSession.user_id == current_user.id))
    fastings = f_res.scalars().all()
    
    bundle = build_patient_bundle(current_user, readings, meals, fastings)
    
    # Return as downloadable JSON file
    return Response(
        content=bundle.json(exclude_none=True, indent=2),
        media_type="application/fhir+json",
        headers={
            "Content-Disposition": f"attachment; filename=fhir_bundle_patient_{current_user.id}.json"
        }
    )
