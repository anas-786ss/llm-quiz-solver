import httpx, asyncio
from ..utils import logger
from typing import Dict, Any

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Extract API URLs and headers from instruction and call them.
    This is a simplified implementation: looks for http(s) urls in instruction and fetches them.
    """
    import re
    instruction = page_info.get("instruction", "")
    urls = re.findall(r"https?://[A-Za-z0-9./?=_-]+", instruction)
    # filter likely api endpoints (not the quiz url)
    urls = [u for u in urls if "submit" not in u and u != page_info.get("url")]
    if not urls:
        return {"worker": "api_sourcing", "error": "no API url found in instruction"}
    # call first url
    api_url = urls[0]
    async with httpx.AsyncClient() as client:
        r = await client.get(api_url, timeout=20)
        r.raise_for_status()
        try:
            data = r.json()
            return {"worker": "api_sourcing", "result": data}
        except Exception:
            return {"worker": "api_sourcing", "text": r.text[:200]}
