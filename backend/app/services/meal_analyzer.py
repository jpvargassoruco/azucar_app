import httpx
import base64
import json
from app.config import settings
import logging
from app.models.user import User
from typing import Optional

logger = logging.getLogger(__name__)

async def analyze_meal_image(image_path: str, user: Optional[User] = None, health_context: str = "") -> dict:
    """
    Sends the meal image to the resolved Vision API (OpenRouter or Kimi).
    Parses and returns structured nutritional details.
    """
    # Resolve credentials, model, and endpoint
    api_key = user.ai_api_key if user and user.ai_api_key else settings.OPENROUTER_API_KEY
    base_url = user.ai_base_url if user and user.ai_base_url else settings.OPENROUTER_BASE_URL
    model = user.ai_model if user and user.ai_model else settings.OPENROUTER_MODEL
    provider = user.ai_provider if user and user.ai_provider else "openrouter"
    
    # Autofill defaults for Kimi
    if user and provider == "kimi" and not user.ai_base_url:
        base_url = "https://api.moonshot.cn/v1"

    if not api_key:
        logger.warning("No API Key configured for meal analysis. Returning fallback.")
        return get_fallback_analysis()
        
    try:
        # Read file and encode to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
        image_data_url = f"data:image/jpeg;base64,{base64_image}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://azucar.aeisoftware.com",
            "X-Title": "Azucar Control"
        }
        
        prompt = (
            "Eres un nutricionista experto en diabetes tipo 2. Analiza esta foto de comida y responde EXCLUSIVAMENTE "
            "con un objeto JSON estructurado que siga exactamente este esquema, sin bloques de código markdown (```json), sin texto adicional:\n"
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
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
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
            
            # Clean markdown formatting if returned by the LLM
            content_cleaned = content.strip()
            if content_cleaned.startswith("```"):
                lines = content_cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content_cleaned = "\n".join(lines).strip()
                
            analysis = json.loads(content_cleaned)
            return analysis
            
    except Exception as ex:
        logger.error(f"Error in Vision analysis: {ex}")
        return get_fallback_analysis()

async def correct_meal_analysis(current_analysis: dict, correction_comment: str, user: Optional[User] = None, health_context: str = "") -> dict:
    """
    Sends the current analysis and user correction comment to the LLM to generate a corrected JSON analysis.
    """
    api_key = user.ai_api_key if user and user.ai_api_key else settings.OPENROUTER_API_KEY
    base_url = user.ai_base_url if user and user.ai_base_url else settings.OPENROUTER_BASE_URL
    model = user.ai_model if user and user.ai_model else settings.OPENROUTER_MODEL
    provider = user.ai_provider if user and user.ai_provider else "openrouter"
    
    if user and provider == "kimi" and not user.ai_base_url:
        base_url = "https://api.moonshot.cn/v1"

    if not api_key:
        logger.warning("No API Key configured for meal analysis. Returning current.")
        return current_analysis
        
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://azucar.aeisoftware.com",
            "X-Title": "Azucar Control"
        }
        
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                
            analysis = json.loads(content_cleaned)
            return analysis
            
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
