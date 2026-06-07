from pywebpush import webpush, WebPushException
from app.config import settings
import logging
import anyio

logger = logging.getLogger(__name__)

async def send_push_notification(endpoint: str, p256dh: str, auth: str, data: str) -> bool:
    """
    Sends a push notification to a browser endpoint using VAPID keys.
    Returns True if successful, False if the subscription is invalid/expired (404/410).
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured. Skipping push notification.")
        return False
        
    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": p256dh,
            "auth": auth
        }
    }
    
    try:
        # Run the blocking pywebpush call in a separate thread to prevent blocking the async loop
        def sync_webpush():
            webpush(
                subscription_info=subscription_info,
                data=data,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": settings.VAPID_MAILTO,
                }
            )
            
        await anyio.to_thread.run_sync(sync_webpush)
        return True
        
    except WebPushException as ex:
        # Handle revoked or expired subscriptions
        if ex.response is not None and ex.response.status_code in (404, 410):
            logger.info(f"Subscription expired (status {ex.response.status_code}). Removing.")
            return False
        logger.error(f"WebPush HTTP error: {ex.response.status_code if ex.response else 'No Response'} - {ex}")
        return False
    except Exception as ex:
        logger.error(f"Unexpected error sending push notification: {ex}")
        return False
