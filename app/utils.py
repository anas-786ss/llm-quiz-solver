import time, logging, httpx
from contextlib import contextmanager
import asyncio
import PyPDF2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("quiz-solver")

@contextmanager
def timer(name="operation"):
    t0 = time.time()
    yield
    logger.info("%s took %.2fs", name, time.time() - t0)

def now_ts():
    return time.time()

async def run_with_timeout(coro, timeout, name="task"):
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        logger.error("%s timed out after %.1fs", name, timeout)
        raise

async def submit_answer(submit_url: str, payload: dict, timeout: int = 20) -> dict:
    """
    Post the answer payload to submit_url and return JSON response (or raise).
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(submit_url, json=payload)
        r.raise_for_status()
        return r.json()

def extract_pdf_text(file_path: str, page_num: int = None) -> str:
    """Extract text from PDF, optionally from specific page"""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        if page_num is not None:
            # Page numbers in questions are 1-indexed
            if page_num <= len(reader.pages):
                return reader.pages[page_num - 1].extract_text()
            return ""
        # Extract all pages
        return "\n".join([page.extract_text() for page in reader.pages])
