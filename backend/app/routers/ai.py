from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.auth.dependencies import get_current_user
from app.services.ai_service import get_user_health_context, query_hermes_agent

router = APIRouter()

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_assistant(
    chat_in: AIChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Interact with the AI assistant (Hermes-Agent).
    Automatically compiles user health statistics to personalize answers.
    """
    # 1. Fetch patient's medical details context
    health_context = await get_user_health_context(db, current_user)
    
    # 2. Call Hermes / OpenRouter with compiled context and history
    response_text = await query_hermes_agent(
        message=chat_in.message,
        history=chat_in.history,
        health_context=health_context,
        user=current_user
    )
    
    return AIChatResponse(response=response_text)
