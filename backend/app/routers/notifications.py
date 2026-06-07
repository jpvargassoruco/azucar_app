from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json
from app.database import get_db
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.schemas.push import PushSubscriptionCreate
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/key")
async def get_vapid_public_key():
    """Retrieve the server's VAPID public key for web push subscription."""
    from app.config import settings
    return {"public_key": settings.VAPID_PUBLIC_KEY}

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_notifications(
    sub_in: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new device/browser push subscription for Web Push notifications."""
    result = await db.execute(
        select(PushSubscription)
        .filter(PushSubscription.endpoint == sub_in.endpoint)
    )
    db_sub = result.scalars().first()
    
    if db_sub:
        db_sub.user_id = current_user.id
        db_sub.p256dh = sub_in.keys.p256dh
        db_sub.auth = sub_in.keys.auth
    else:
        db_sub = PushSubscription(
            user_id=current_user.id,
            endpoint=sub_in.endpoint,
            p256dh=sub_in.keys.p256dh,
            auth=sub_in.keys.auth
        )
        db.add(db_sub)
        
    await db.commit()
    await db.refresh(db_sub)
    return {"status": "subscribed", "id": db_sub.id}

@router.post("/test")
async def send_test_notification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a real-time test notification to all registered subscriptions for the user."""
    from app.services.push_service import send_push_notification
    
    result = await db.execute(
        select(PushSubscription)
        .filter(PushSubscription.user_id == current_user.id)
    )
    subscriptions = result.scalars().all()
    
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes ningún dispositivo registrado para recibir notificaciones."
        )
        
    payload = {
        "title": "Prueba de Azúcar Control",
        "body": "¡Hola! Las notificaciones Push están configuradas correctamente.",
        "icon": "/icons/icon-192x192.png",
        "badge": "/icons/icon-192x192.png",
        "url": "/#stats"
    }
    
    success_count = 0
    for sub in subscriptions:
        success = await send_push_notification(
            endpoint=sub.endpoint,
            p256dh=sub.p256dh,
            auth=sub.auth,
            data=json.dumps(payload)
        )
        if success:
            success_count += 1
        else:
            # If subscription is dead (e.g. 410 Gone), delete it
            await db.delete(sub)
            
    await db.commit()
    return {
        "status": "enviado",
        "sent_count": success_count,
        "deleted_count": len(subscriptions) - success_count
    }
