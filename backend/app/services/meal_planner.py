import httpx
import json
from app.config import settings
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

async def generate_meal_plan(health_context: str, preferences: str, num_meals: int, user: User) -> dict:
    """
    Generates a personalized meal plan using the LLM based on health context and preferences.
    """
    api_key = user.ai_api_key if user and user.ai_api_key else settings.OPENROUTER_API_KEY
    base_url = user.ai_base_url if user and user.ai_base_url else settings.OPENROUTER_BASE_URL
    model = user.ai_model if user and user.ai_model else settings.OPENROUTER_MODEL
    provider = user.ai_provider if user and user.ai_provider else "openrouter"
    
    if user and provider == "kimi" and not user.ai_base_url:
        base_url = "https://api.moonshot.cn/v1"

    if not api_key:
        raise ValueError("No API Key configured for meal planner.")
        
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://azucar.aeisoftware.com",
            "X-Title": "Azucar Control"
        }
        
        pref_str = f"Preferencias o restricciones: {preferences}" if preferences else "Sin restricciones particulares."
        
        prompt = (
            "Eres un nutricionista experto en diabetes tipo 2. Diseña un plan de comidas de 1 día para este paciente.\n\n"
            f"CONTEXTO DE SALUD DEL PACIENTE:\n{health_context}\n\n"
            f"PREFERENCIAS:\n{pref_str}\n"
            f"CANTIDAD DE COMIDAS SOLICITADAS: {num_meals}\n\n"
            "Responde EXCLUSIVAMENTE con un objeto JSON estructurado que siga exactamente este esquema, sin bloques de código markdown, sin texto adicional:\n"
            "{\n"
            "  \"plan_date\": \"YYYY-MM-DD\",\n"
            "  \"meals\": [\n"
            "    {\n"
            "      \"meal_type\": \"desayuno|almuerzo|cena|merienda\",\n"
            "      \"time_suggestion\": \"HH:MM\",\n"
            "      \"description\": \"descripción del plato\",\n"
            "      \"estimated_calories\": número,\n"
            "      \"estimated_carbs_g\": número,\n"
            "      \"glycemic_impact\": \"bajo|moderado|alto\",\n"
            "      \"reasoning\": \"por qué es bueno para el paciente\"\n"
            "    }\n"
            "  ],\n"
            "  \"daily_summary\": {\n"
            "    \"total_calories\": número,\n"
            "    \"total_carbs_g\": número\n"
            "  },\n"
            "  \"tips\": [\"consejo 1\", \"consejo 2\"]\n"
            "}"
        )
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            res_json = response.json()
            
            content = res_json["choices"][0]["message"]["content"]
            
            content_cleaned = content.strip()
            if content_cleaned.startswith("```"):
                lines = content_cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content_cleaned = "\n".join(lines).strip()
                
            plan = json.loads(content_cleaned)
            return plan
            
    except Exception as ex:
        logger.error(f"Error generating meal plan: {ex}")
        raise ValueError(f"Error generando plan: {ex}")
