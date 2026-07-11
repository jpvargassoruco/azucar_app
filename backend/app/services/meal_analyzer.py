import base64
import json
from app.config import settings
import logging
from app.models.user import User
from app.services.ai_providers import call_ai
from typing import Optional

logger = logging.getLogger(__name__)

async def analyze_meal_image(image_path: str, user: Optional[User] = None, health_context: str = "") -> dict:
    """
    Sends the meal image to the user's AI provider for nutritional analysis.
    For Deepseek (text-only), falls back to system OpenRouter for vision.
    """
    if not (user and user.ai_api_key) and not settings.OPENROUTER_API_KEY:
        logger.warning("No API Key configured for meal analysis. Returning fallback.")
        return get_fallback_analysis()

    try:
        # Read file and encode to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        image_data_url = f"data:image/jpeg;base64,{base64_image}"

        prompt = (
            "Eres un nutricionista experto en diabetes tipo 2. Analiza esta foto de comida y responde EXCLUSIVAMENTE "
            "con un objeto JSON estructurado que siga exactamente este esquema, sin bloques de código markdown, sin texto adicional:\n"
            "{\n"
            "  \"food_items\": [\"lista de alimentos identificados\"],\n"
            "  \"calories_estimated\": número,\n"
            "  \"carbs_g\": número,\n"
            "  \"protein_g\": número,\n"
            "  \"fat_g\": número,\n"
            "  \"fiber_g\": número,\n"
            "  \"glycemic_impact\": \"bajo|moderado|alto\",\n"
            "  \"recommendation\": \"consejo breve de nutrición para un paciente con diabetes tipo 2\"\n"
            "}\n"
        )
        if health_context:
            prompt += f"\nCONTEXTO DE SALUD DEL PACIENTE:\n{health_context}\n"

        # For Deepseek (text-only), force fallback to system OpenRouter
        provider = user.ai_provider if user and user.ai_provider else "openrouter"
        if provider == "deepseek":
            logger.info("Deepseek is text-only. Using system OpenRouter for vision analysis.")
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_data_url}}]}]
            content = await call_ai(messages, None, json_mode=True, use_fallback=True)
        else:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_data_url}}]}]
            content = await call_ai(messages, user, json_mode=True, use_fallback=True)

        # Clean markdown formatting
        content_cleaned = content.strip()
        if content_cleaned.startswith("```"):
            lines = content_cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content_cleaned = "\n".join(lines).strip()

        return json.loads(content_cleaned)

    except Exception as ex:
        logger.error(f"Error in Vision analysis: {ex}")
        return get_fallback_analysis()

async def correct_meal_analysis(current_analysis: dict, correction_comment: str, user: Optional[User] = None, health_context: str = "") -> dict:
    """
    Sends the current analysis and user correction comment to the LLM to generate a corrected JSON analysis.
    """
    if not (user and user.ai_api_key) and not settings.OPENROUTER_API_KEY:
        logger.warning("No API Key configured for meal correction. Returning current.")
        return current_analysis

    try:
        prompt = (
            "Eres un nutricionista experto en diabetes tipo 2. El usuario ha proveído una corrección para el análisis nutricional de una comida reciente.\n"
            f"El análisis anterior era:\n{json.dumps(current_analysis, indent=2, ensure_ascii=False)}\n\n"
            f"El usuario comenta lo siguiente sobre la comida: \"{correction_comment}\"\n\n"
            "Por favor corrige el análisis considerando el comentario del usuario y devuelve EXCLUSIVAMENTE el objeto JSON estructurado actualizado. "
            "No incluyas bloques de código markdown, solo el JSON:\n"
            "{\n"
            "  \"food_items\": [\"lista de alimentos identificados\"],\n"
            "  \"calories_estimated\": número,\n"
            "  \"carbs_g\": número,\n"
            "  \"protein_g\": número,\n"
            "  \"fat_g\": número,\n"
            "  \"fiber_g\": número,\n"
            "  \"glycemic_impact\": \"bajo|moderado|alto\",\n"
            "  \"recommendation\": \"consejo breve de nutrición para un paciente con diabetes tipo 2\"\n"
            "}"
        )

        if health_context:
            prompt += f"\n\nCONTEXTO DE SALUD DEL PACIENTE:\n{health_context}"

        messages = [{"role": "user", "content": prompt}]
        content = await call_ai(messages, user, json_mode=True, use_fallback=True)

        content_cleaned = content.strip()
        if content_cleaned.startswith("```"):
            lines = content_cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content_cleaned = "\n".join(lines).strip()

        return json.loads(content_cleaned)

    except Exception as ex:
        logger.error(f"Error in meal correction: {ex}")
        return current_analysis


def get_fallback_analysis() -> dict:
    return {
        "food_items": ["Alimento no identificado (Fallback)"],
        "calories_estimated": 350,
        "carbs_g": 30,
        "protein_g": 15,
        "fat_g": 10,
        "fiber_g": 3,
        "glycemic_impact": "moderado",
        "recommendation": "No se pudo conectar con el servicio de análisis de IA. Por favor, verifica tu OpenRouter API Key."
    }
