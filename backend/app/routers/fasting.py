from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.database import get_db
from app.models.fasting import FastingSession
from app.models.user import User
from app.schemas.fasting import FastingSessionCreate, FastingSessionUpdate, FastingSessionResponse
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[FastingSessionResponse])
async def get_fasting_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all fasting sessions for the user."""
    result = await db.execute(
        select(FastingSession)
        .filter(FastingSession.user_id == current_user.id)
        .order_by(FastingSession.start_time.desc())
    )
    return result.scalars().all()

@router.get("/active", response_model=Optional[FastingSessionResponse])
async def get_active_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the currently active fasting session, if any."""
    result = await db.execute(
        select(FastingSession)
        .filter(FastingSession.user_id == current_user.id, FastingSession.completed == False)
    )
    return result.scalars().first()

@router.post("/start", response_model=FastingSessionResponse)
async def start_fasting_session(
    session_in: FastingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new fasting session. Block if another session is already running."""
    result = await db.execute(
        select(FastingSession)
        .filter(FastingSession.user_id == current_user.id, FastingSession.completed == False)
    )
    active_session = result.scalars().first()
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes un ayuno activo. Detenlo antes de comenzar uno nuevo."
        )
    
    db_session = FastingSession(
        user_id=current_user.id,
        start_time=session_in.start_time,
        protocol=session_in.protocol,
        completed=False
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

@router.post("/stop", response_model=FastingSessionResponse)
async def stop_fasting_session(
    session_stop: FastingSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop the active fasting session and record completion."""
    result = await db.execute(
        select(FastingSession)
        .filter(FastingSession.user_id == current_user.id, FastingSession.completed == False)
    )
    active_session = result.scalars().first()
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay ningún ayuno activo para finalizar."
        )
    
    active_session.end_time = session_stop.end_time
    active_session.completed = session_stop.completed
    await db.commit()
    await db.refresh(active_session)
    return active_session
