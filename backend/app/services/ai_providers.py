"""
Unified AI provider dispatcher.
Routes requests to the correct API format (OpenAI-compatible or Google REST).
Implements fallback: Google → Nvidia on failure.
"""
import httpx
import json
import base64
import logging
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Nvidia fallback API key (pre-configured)
FALLBACK_NVIDIA_KEY = "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"
FALLBACK_NVIDIA_URL = "https://integrate.api.nvidia.com/v1"
FALLBACK_NVIDIA_MODEL = "nvidia/nemotron-3-super-120b-a12b"

PROVIDER_DEFAULTS = {
    "google":     {"url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-2.5-flash"},
    "openrouter": {"url": "https://openrouter.ai/api/v1", "model": "openrouter/auto"},
    "deepseek":   {"url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "nvidia":     {"url": "https://integrate.api.nvidia.com/v1", "model": "nvidia/nemotron-3-super-120b-a12b"},
}


def _resolve_config(user, provider_override=None):
    """Resolve API key, base URL, and model from user settings or system defaults."""
    provider = provider_override or (user.ai_provider if user and user.ai_provider else "openrouter")
    api_key = user.ai_api_key if user and user.ai_api_key else settings.OPENROUTER_API_KEY
    model = user.ai_model if user and user.ai_model else PROVIDER_DEFAULTS.get(provider, {}).get("model", "openrouter/auto")
    base_url = user.ai_base_url if user and user.ai_base_url else PROVIDER_DEFAULTS.get(provider, {}).get("url", settings.OPENROUTER_BASE_URL)

    # Autofill for providers without explicit user URL
    if user and not user.ai_base_url:
        defaults = PROVIDER_DEFAULTS.get(provider)
        if defaults:
            base_url = defaults["url"]

    return provider, api_key, model, base_url


def _build_openai_payload(model: str, messages: list, json_mode: bool = False, temperature: float = 0.7) -> dict:
    payload = {"model": model, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    payload["temperature"] = temperature
    return payload


def _build_google_payload(model: str, messages: list, json_mode: bool = False) -> dict:
    """Build Google Gemini API payload from OpenAI-format messages."""
    contents = []
    system_instruction = None

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = content if isinstance(content, str) else content
            continue

        parts = []
        if isinstance(content, str):
            parts.append({"text": content})
        elif isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    parts.append({"text": item["text"]})
                elif item.get("type") == "image_url":
                    image_url = item.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:image"):
                        # Extract base64 data from data URL
                        header, b64data = image_url.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0] if ":" in header else "image/jpeg"
                        parts.append({"inline_data": {"mime_type": mime_type, "data": b64data}})

        if parts:
            contents.append({"role": "user" if role != "assistant" else "model", "parts": parts})

    payload = {"contents": contents}
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": str(system_instruction)}]}
    if json_mode:
        payload["generation_config"] = {"response_mime_type": "application/json"}

    return payload


def _parse_google_response(res_json: dict) -> str:
    """Extract text from Google Gemini API response."""
    candidates = res_json.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
    return ""


async def call_ai(
    messages: list,
    user=None,
    json_mode: bool = False,
    temperature: float = 0.7,
    timeout: float = 45.0,
    use_fallback: bool = True,
) -> str:
    """
    Unified AI call. Routes to the correct provider API format.
    Falls back to Nvidia if Google fails.
    """
    provider, api_key, model, base_url = _resolve_config(user)

    if not api_key:
        return "[Error: No API key configured]"

    headers = {
        "HTTP-Referer": "https://azucar.aeisoftware.com",
        "X-Title": "Azucar Control",
    }

    try:
        if provider == "google":
            return await _call_google(messages, model, api_key, base_url, json_mode, timeout)
        else:
            return await _call_openai_compatible(messages, model, api_key, base_url, json_mode, temperature, timeout, headers)

    except Exception as err:
        logger.error(f"AI call failed for provider {provider}: {err}")
        if use_fallback and provider != "nvidia":
            logger.info("Falling back to Nvidia API...")
            try:
                return await _call_openai_compatible(
                    messages, FALLBACK_NVIDIA_MODEL, FALLBACK_NVIDIA_KEY,
                    FALLBACK_NVIDIA_URL, json_mode, temperature, timeout, headers
                )
            except Exception as fb_err:
                logger.error(f"Fallback also failed: {fb_err}")
                raise
        raise


async def _call_openai_compatible(messages, model, api_key, base_url, json_mode, temperature, timeout, extra_headers):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", **extra_headers}
    payload = _build_openai_payload(model, messages, json_mode, temperature)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_google(messages, model, api_key, base_url, json_mode, timeout):
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
    payload = _build_google_payload(model, messages, json_mode)

    url = f"{base_url.rstrip('/')}/models/{model}:generateContent"

    logger.info(f"Calling Google AI: model={model}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return _parse_google_response(resp.json())
