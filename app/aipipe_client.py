import os, json, logging
import httpx
from typing import Any, Dict, Optional
from .config import AIPIPE_TOKEN

logger = logging.getLogger("aipipe-client")

AIPIPE_OPENROUTER_URL = "https://aipipe.org/openrouter/v1/responses"
GEMINI_BASE = "https://aipipe.org/geminiv1beta"

HEADERS = {}
if AIPIPE_TOKEN:
    HEADERS = {"Authorization": f"Bearer {AIPIPE_TOKEN}", "Content-Type": "application/json"}
else:
    logger.warning("AIPIPE_TOKEN not set — AiPipe calls will be skipped or mocked.")

async def ask_openai(prompt: str, model: str = "openai/gpt-4o-mini", timeout: int = 30) -> Optional[Dict[str, Any]]:
    if not AIPIPE_TOKEN:
        logger.warning("Skipping AiPipe call: no token")
        return None
    payload = {"model": model, "input": prompt}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(AIPIPE_OPENROUTER_URL, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()

async def call_gemini(payload: Dict[str, Any], path: str = "models/gemini-1.5-flash:generateContent", timeout: int = 30) -> Optional[Dict[str, Any]]:
    if not AIPIPE_TOKEN:
        logger.warning("Skipping Gemini call: no token")
        return None
    url = f"{GEMINI_BASE}/{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()

async def run_llm(prompt: str, timeout: int = 30) -> str:
    """
    Use AiPipe to run LLM inference; try OpenRouter then fallback to Gemini.
    Returns a plain string (may be empty on failure).
    """
    if not AIPIPE_TOKEN:
        logger.warning("No AIPIPE_TOKEN, returning empty")
        return ""
    try:
        # Try OpenRouter (OpenAI-compatible)
        result = await ask_openai(prompt, model="openai/gpt-4o-mini", timeout=timeout)
        # The AiPipe response shape may vary; try common fields
        if result:
            # Some versions return { output: "text" }
            if isinstance(result, dict) and "output" in result and isinstance(result["output"], str):
                return result["output"].strip()
            # Others return choices-like structure
            if "data" in result and isinstance(result["data"], dict):
                out = result["data"].get("output") or result["data"].get("text")
                if isinstance(out, str):
                    return out.strip()
        # Fallback to Gemini
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        g = await call_gemini(payload, timeout=timeout)
        if g and "candidates" in g and g["candidates"]:
            try:
                return g["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                pass
        return ""
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ""
