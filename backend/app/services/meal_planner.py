import json
from app.config import settings
from app.models.user import User
from app.services.ai_providers import call_ai
import logging

logger = logging.getLogger(__name__)

async def generate_meal_plan(health_context: str, preferences: str, num_meals: int, user: User) -> dict:
    """
    Generates a personalized meal plan using the LLM based on health context and preferences.
    """
    if not (user and user.ai_api_key) and not settings.OPENROUTER_API_KEY:
        raise ValueError("No API Key configured for meal planner.")

    try:
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

        messages = [{"role": "user", "content": prompt}]
        content = await call_ai(messages, user, json_mode=True)

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
