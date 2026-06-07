import httpx
from app.config import settings
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.glucose import GlucoseReading
from app.models.habit import HabitLog
from app.models.fasting import FastingSession
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

async def get_user_health_context(db: AsyncSession, user: User) -> str:
    """
    Compiles recent health metrics for the user to inject as context into the AI system prompt.
    """
    # 1. Fetch latest 5 glucose readings
    gl_result = await db.execute(
        select(GlucoseReading)
        .filter(GlucoseReading.user_id == user.id)
        .order_by(GlucoseReading.datetime.desc())
        .limit(5)
    )
    readings = gl_result.scalars().all()
    
    readings_str = ""
    if readings:
        for r in readings:
            dt_str = r.datetime.strftime("%Y-%m-%d %H:%M")
            readings_str += f"- {dt_str}: {r.value_mgdl} mg/dL ({r.condition})\n"
    else:
        readings_str = "No hay lecturas de glucosa registradas aún.\n"
        
    # 2. Fetch today's habits status
    today = date.today()
    h_result = await db.execute(
        select(HabitLog)
        .filter(HabitLog.user_id == user.id, HabitLog.date == today)
    )
    logs = h_result.scalars().all()
    habits_str = ""
    for log in logs:
        habits_str += f"- {log.habit_key}: {'Completado' if log.completed else 'Pendiente'}\n"
    if not logs:
        habits_str = "Ninguno completado aún hoy.\n"
        
    # 3. Fetch active fasting session
    f_result = await db.execute(
        select(FastingSession)
        .filter(FastingSession.user_id == user.id, FastingSession.completed == False)
    )
    active_fast = f_result.scalars().first()
    fast_str = "No hay ayuno activo en curso.\n"
    if active_fast:
        fast_str = f"Ayuno activo iniciado a las {active_fast.start_time.strftime('%Y-%m-%d %H:%M')} bajo el protocolo {active_fast.protocol}.\n"
        
    context = (
        f"INFORMACIÓN DEL PACIENTE:\n"
        f"- Nombre: {user.name}\n"
        f"- Condición: Diabetes Tipo 2\n"
        f"- Fecha actual: {date.today().strftime('%Y-%m-%d')}\n\n"
        f"ÚLTIMAS LECTURAS DE GLUCOSA:\n{readings_str}\n"
        f"ESTADO DE HÁBITOS DIARIOS DE HOY:\n{habits_str}\n"
        f"ESTADO DE AYUNO INTERMITENTE:\n{fast_str}\n"
        f"Instrucciones: Utiliza este contexto para dar recomendaciones de salud personalizadas, "
        f"científicas y alentadoras en Español. Si los niveles de glucosa superan 250 mg/dL, "
        f"recomienda fuertemente la hidratación con agua, evitar ejercicio pesado de inmediato "
        f"y vigilar síntomas de crisis."
    )
    return context

async def query_hermes_agent(message: str, history: list, health_context: str) -> str:
    """
    Dispatches chat request to Hermes-Agent container with fallback to direct OpenRouter.
    """
    if not settings.OPENROUTER_API_KEY:
        return (
            "El Asistente de IA no está configurado. Falta la variable OPENROUTER_API_KEY "
            "en el archivo de configuración (.env) del servidor."
        )
        
    # Set system prompt
    messages = [
        {
            "role": "system",
            "content": (
                "Eres Hermes-Health, un asistente virtual experto en nutrición y entrenamiento para "
                "pacientes con Diabetes Tipo 2. Responde en Español de manera clara y motivadora.\n\n"
                f"CONTEXTO DE SALUD DEL PACIENTE:\n{health_context}"
            )
        }
    ]
    
    # Append history
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    # Append latest user query
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {settings.HERMES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            # 1. Attempt connection to Hermes-Agent container
            response = await client.post(
                f"{settings.HERMES_URL}/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            res_data = response.json()
            return res_data["choices"][0]["message"]["content"]
            
        except Exception as hermes_err:
            logger.info(f"Hermes Agent container unreachable ({hermes_err}). Falling back to direct OpenRouter API.")
            
            # 2. Fallback to direct OpenRouter API call
            or_headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://azucar.aeisoftware.com",
                "X-Title": "Azucar Control"
            }
            
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=or_headers,
                    json=payload
                )
                response.raise_for_status()
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
            except Exception as or_err:
                logger.error(f"Direct OpenRouter API call failed: {or_err}")
                return "Lo siento, en este momento no puedo conectarme con los servidores de Inteligencia Artificial. Por favor intenta más tarde."
