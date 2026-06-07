import asyncio
import json
import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis
from app.config import settings
from app.models.push_subscription import PushSubscription
from app.services.push_service import send_push_notification

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("notification_worker")

async def process_notifications():
    """
    Worker loop that pulls notifications from Redis queue 'notifications_queue'
    and dispatches them to registered browser push endpoints.
    """
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(db_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Connect to Redis async
    r = Redis.from_url(settings.REDIS_URL)
    logger.info("Notification Worker started. Listening on 'notifications_queue'...")
    
    while True:
        try:
            # BLPOP blocks until an item is available in the list
            res = await r.blpop("notifications_queue", timeout=5)
            if not res:
                continue
                
            _, payload_bytes = res
            logger.info("De-queued a notification job.")
            
            job = json.loads(payload_bytes.decode("utf-8"))
            user_id = job.get("user_id")
            title = job.get("title", "Azúcar Control")
            body = job.get("body", "")
            url = job.get("url", "/")
            
            if not user_id:
                logger.error("Skipped job: missing user_id field.")
                continue
                
            async with SessionLocal() as db:
                # Retrieve all active push endpoints for the targeted user
                result = await db.execute(
                    select(PushSubscription).filter(PushSubscription.user_id == user_id)
                )
                subscriptions = result.scalars().all()
                
                if not subscriptions:
                    logger.info(f"No push subscriptions registered for user {user_id}. Skipped.")
                    continue
                    
                notification_payload = json.dumps({
                    "title": title,
                    "body": body,
                    "icon": "/icons/icon-192x192.png",
                    "badge": "/icons/icon-192x192.png",
                    "url": url
                })
                
                for sub in subscriptions:
                    # Trigger webpush dispatch
                    success = await send_push_notification(
                        endpoint=sub.endpoint,
                        p256dh=sub.p256dh,
                        auth=sub.auth,
                        data=notification_payload
                    )
                    
                    if not success:
                        logger.info(f"Push subscription ID {sub.id} returned expired. Deleting from DB.")
                        await db.delete(sub)
                
                await db.commit()
                
        except asyncio.CancelledError:
            logger.info("Worker cancel request received. Stopping worker loop.")
            break
        except Exception as ex:
            logger.error(f"Error encountered in worker main loop: {ex}")
            await asyncio.sleep(2)  # Avoid fast-spinning loops on connection drop
            
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(process_notifications())
    except KeyboardInterrupt:
        logger.info("Worker terminated by user interrupt.")
