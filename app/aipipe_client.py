import logging, json
import httpx
from typing import Any, Dict, Optional
from .config import AIPIPE_TOKEN

logger = logging.getLogger("aipipe-client")

AIPIPE_OPENROUTER_URL = "https://aipipe.org/openrouter/v1/responses"

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
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(AIPIPE_OPENROUTER_URL, headers=HEADERS, json=payload)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        body = e.response.text if e.response is not None else ""
        logger.error("OpenRouter HTTP error %s: %s", e.response.status_code if e.response else "?", body[:500])
        return None
    except Exception as e:
        logger.error("OpenRouter call failed: %s", e)
        return None

def _extract_text_from_openai_like(resp: Dict[str, Any]) -> str:
    if not isinstance(resp, dict):
        return ""
    # Common shapes
    out = resp.get("output")
    if isinstance(out, str) and out.strip():
        return out.strip()
    data = resp.get("data")
    if isinstance(data, dict):
        for k in ("output", "text", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        choices = data.get("choices") or data.get("outputs")
        if isinstance(choices, list) and choices:
            c0 = choices[0]
            if isinstance(c0, dict):
                msg = c0.get("message", {})
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                for k in ("text", "output", "content"):
                    v = c0.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
    choices = resp.get("choices")
    if isinstance(choices, list) and choices:
        c0 = choices[0]
        if isinstance(c0, dict):
            msg = c0.get("message", {})
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            for k in ("text", "output", "content"):
                v = c0.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
    for k in ("text", "content"):
        v = resp.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

async def run_llm(prompt: str, timeout: int = 30) -> str:
    """
    Use AiPipe (OpenRouter) to run LLM inference. Returns plain text (or empty on failure).
    """
    if not AIPIPE_TOKEN:
        logger.warning("No AIPIPE_TOKEN, returning empty")
        return ""
    result = await ask_openai(prompt, model="openai/gpt-4o-mini", timeout=timeout)
    if result:
        text = _extract_text_from_openai_like(result)
        if text:
            return text
        logger.warning("OpenRouter response had no extractable text; sample: %s", json.dumps(result)[:500])
    return ""
