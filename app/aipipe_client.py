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

async def ask_openai(prompt: str, model: str = "openai/gpt-4.1-nano", timeout: int = 30) -> Optional[Dict[str, Any]]:
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
