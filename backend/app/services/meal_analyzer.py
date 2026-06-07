import httpx
import base64
import json
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def analyze_meal_image(image_path: str) -> dict:
    """
    Sends the meal image to the OpenRouter Vision API.
    Parses and returns structured nutritional details.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not configured. Returning fallback placeholder analysis.")
        return get_fallback_analysis()
        
    try:
        # Read file and encode to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
        image_data_url = f"data:image/jpeg;base64,{base64_image}"
        
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
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
            "}"
        )
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
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
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
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
        logger.error(f"Error in OpenRouter Vision analysis: {ex}")
        return get_fallback_analysis()

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
