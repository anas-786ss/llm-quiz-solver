import httpx, asyncio, re
from ..utils import logger
from typing import Dict, Any

def _sanitize_url(u: str) -> str:
    # Remove trailing punctuation accidentally captured
    return u.rstrip(".,;:()[]{}<>\"' \n\t\r")

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Extract API URLs and headers from instruction and call them.
    Simplified: finds http(s) URLs in instruction and tries them in order.
    Handles HTTP errors gracefully and returns partial data or error without raising.
    """
    instruction = page_info.get("instruction", "") or ""
    urls = re.findall(r"https?://[A-Za-z0-9./?=_\-]+", instruction)
    urls = [u for u in urls if "submit" not in u and u != page_info.get("url")]
    urls = [_sanitize_url(u) for u in urls]

    if not urls:
        return {"worker": "api_sourcing", "error": "no API url found in instruction"}

    async with httpx.AsyncClient() as client:
        for api_url in urls:
            try:
                r = await client.get(api_url, timeout=20)
                # If 404/500, continue to next URL
                if r.status_code >= 400:
                    logger.warning("API sourcing got %s for %s", r.status_code, api_url)
                    continue
                # Try JSON first
                try:
                    data = r.json()
                    return {"worker": "api_sourcing", "url": api_url, "result": data}
                except Exception:
                    text = r.text[:500]
                    return {"worker": "api_sourcing", "url": api_url, "text": text}
            except httpx.HTTPError as e:
                logger.warning("API sourcing error for %s: %s", api_url, e)
                continue

    return {"worker": "api_sourcing", "error": "all candidate API urls failed"}
