from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
import os
import uuid
from typing import List, Optional
from app.database import get_db
from app.models.meal import MealEntry
from app.models.user import User
from app.schemas.meal import MealEntryResponse
from app.auth.dependencies import get_current_user
from app.services.image_service import compress_to_thumbnail
from app.services.meal_analyzer import analyze_meal_image

router = APIRouter()

# Directory for storing processed meal photos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[MealEntryResponse])
async def get_meals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all logged meals with their nutritional analysis for the user."""
    result = await db.execute(
        select(MealEntry)
        .filter(MealEntry.user_id == current_user.id)
        .order_by(MealEntry.datetime.desc())
    )
    return result.scalars().all()

@router.post("/upload", response_model=MealEntryResponse, status_code=status.HTTP_201_CREATED)
async def upload_meal(
    photo: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a meal photo. Analyzes the content using Vision AI,
    creates a compressed thumbnail, deletes the original image, and saves to database.
    """
    # Verify file extension
    _, ext = os.path.splitext(photo.filename)
    if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen no soportado. Por favor sube archivos JPG, PNG o WebP."
        )
        
    unique_id = uuid.uuid4().hex
    temp_filename = f"temp_{unique_id}{ext}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)
    
    try:
        # Save uploaded file temporarily to disk for processing
        with open(temp_path, "wb") as f:
            content = await photo.read()
            f.write(content)
            
        # Run Vision API analysis on resolved AI provider
        analysis_result = await analyze_meal_image(temp_path, user=current_user)
        
        # Compress and save thumbnail
        thumbnail_path = compress_to_thumbnail(temp_path, UPLOAD_DIR, f"{unique_id}{ext}")
        
    except Exception as ex:
        # Make sure to cleanup temp file if error occurs
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la foto de comida: {ex}"
        )
    finally:
        # Delete original heavy image
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # Nginx will serve UPLOAD_DIR under /uploads/
    web_thumb_path = f"/uploads/{os.path.basename(thumbnail_path)}"
    
    db_meal = MealEntry(
        user_id=current_user.id,
        datetime=datetime.now(timezone.utc),
        photo_path=None,  # We don't save the original
        thumbnail_path=web_thumb_path,
        notes=notes,
        ai_analysis=analysis_result
    )
    db.add(db_meal)
    await db.commit()
    await db.refresh(db_meal)
    return db_meal

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a meal entry and its associated thumbnail from disk."""
    result = await db.execute(
        select(MealEntry)
        .filter(MealEntry.id == meal_id, MealEntry.user_id == current_user.id)
    )
    meal = result.scalars().first()
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comida no encontrada o no tienes permisos para eliminarla."
        )
        
    # Delete thumbnail file from disk if it exists
    if meal.thumbnail_path:
        filename = os.path.basename(meal.thumbnail_path)
        disk_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.exists(disk_path):
                os.remove(disk_path)
        except Exception as ex:
            # We can log this to console or warnings
            import logging
            logging.getLogger(__name__).warning(f"No se pudo eliminar el archivo {disk_path}: {ex}")
            
    await db.delete(meal)
    await db.commit()
    return

