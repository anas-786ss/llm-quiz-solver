import httpx, os, logging
from ..config import DOWNLOAD_MAX_BYTES
from ..utils import logger

async def download_file(url: str, dest_path: str, timeout: int = 60):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, follow_redirects=True)
        r.raise_for_status()
        content = r.content
        if len(content) > DOWNLOAD_MAX_BYTES:
            raise ValueError("Download exceeds max size")
        with open(dest_path, "wb") as f:
            f.write(content)
    return dest_path
