import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
import asyncpg
from redis.asyncio import Redis

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("check_reminders")

# Fetch environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Ensure DB URL is compatible with asyncpg (postgresql:// -> postgresql+asyncpg:// but asyncpg needs postgresql:// without ORM suffix)
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql://"):
        pass

async def check_alarms():
    """
    Checks if there are any active alarms matching the current hour and minute
    in Bolivia timezone (UTC-4) and schedules push notifications for them.
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL env variable is not set. Exiting.")
        return

    # 1. Calculate current local time in Bolivia (UTC-4)
    tz_bolivia = timezone(timedelta(hours=-4))
    now_local = datetime.now(timezone.utc).astimezone(tz_bolivia)
    current_time_str = now_local.strftime("%H:%M")
    
    logger.info(f"Checking alarms matching local time: {current_time_str}")
    
    conn = None
    redis_client = None
    try:
        # Connect to Postgres
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Connect to Redis
        redis_client = Redis.from_url(REDIS_URL)
        
        # Query active alarms matching current time
        query = """
            SELECT a.id, a.user_id, a.type, a.config_time, u.name 
            FROM alarms a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.is_active = true AND a.config_time = $1
        """
        active_alarms = await conn.fetch(query, current_time_str)
        
        if not active_alarms:
            logger.info("No active alarms matched the current minute.")
            return

        logger.info(f"Found {len(active_alarms)} matching active alarms.")
        
        for alarm in active_alarms:
            alarm_id = alarm["id"]
            user_id = alarm["user_id"]
            alarm_type = alarm["type"]
            user_name = alarm["name"]
            
            title = "Azúcar Control"
            body = "Recordatorio de salud"
            url = "/"
            
            if alarm_type == "metformina":
                title = "💊 Tomar Metformina"
                body = f"Hola {user_name}, es momento de tomar tu dosis de Metformina. Recuerda acompañarla con comida."
                url = "/#alarms"
            elif alarm_type == "postprandial":
                title = "🩸 Medir Glucosa Postprandial"
                body = f"Hola {user_name}, han pasado 2 horas desde tu comida. Es momento de medir tu nivel de glucosa."
                url = "/#registry"
                
                # Deactivate one-time postprandial alarms so they don't trigger daily
                await conn.execute("UPDATE alarms SET is_active = false WHERE id = $1", alarm_id)
                logger.info(f"Deactivated postprandial alarm ID {alarm_id} after triggering.")
            else:
                # Fallback
                body = f"Recordatorio de tu alarma de {alarm_type}."
                
            # Queue the notification job
            job_payload = {
                "user_id": user_id,
                "title": title,
                "body": body,
                "url": url
            }
            
            await redis_client.rpush("notifications_queue", json.dumps(job_payload))
            logger.info(f"Queued notification for user ID {user_id} (Type: {alarm_type})")
            
    except Exception as ex:
        logger.error(f"Error checking alarms: {ex}")
    finally:
        if conn:
            await conn.close()
        if redis_client:
            await redis_client.close()

async def check_medications():
    """
    Checks if there are any active medications/supplements with a dose scheduled
    for the current local time (Bolivia, UTC-4) and weekday, and queues push notifications.
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL env variable is not set. Exiting.")
        return

    tz_bolivia = timezone(timedelta(hours=-4))
    now_local = datetime.now(timezone.utc).astimezone(tz_bolivia)
    current_time_str = now_local.strftime("%H:%M")
    current_weekday = now_local.weekday()

    logger.info(f"Checking medications matching local time: {current_time_str} (weekday {current_weekday})")

    conn = None
    redis_client = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        redis_client = Redis.from_url(REDIS_URL)

        query = """
            SELECT m.id, m.user_id, m.name, m.kind, m.times, m.days_of_week, u.name AS user_name
            FROM medications m
            JOIN users u ON m.user_id = u.id
            WHERE m.is_active = true
        """
        active_medications = await conn.fetch(query)

        matching = [
            row for row in active_medications
            if current_weekday in json.loads(row["days_of_week"]) and current_time_str in json.loads(row["times"])
        ]

        if not matching:
            logger.info("No active medications matched the current minute.")
            return

        logger.info(f"Found {len(matching)} matching medication doses.")

        for row in matching:
            user_id = row["user_id"]
            name = row["name"]
            kind = row["kind"]
            user_name = row["user_name"]

            emoji = "💊" if kind == "medication" else "🌿"
            label = "medicamento" if kind == "medication" else "suplemento"

            job_payload = {
                "user_id": user_id,
                "title": f"{emoji} Tomar {name}",
                "body": f"Hola {user_name}, es momento de tomar tu {label} {name}.",
                "url": "/#medications"
            }

            await redis_client.rpush("notifications_queue", json.dumps(job_payload))
            logger.info(f"Queued medication notification for user ID {user_id} (Medication: {name})")

    except Exception as ex:
        logger.error(f"Error checking medications: {ex}")
    finally:
        if conn:
            await conn.close()
        if redis_client:
            await redis_client.close()

if __name__ == "__main__":
    asyncio.run(check_alarms())
    asyncio.run(check_medications())
