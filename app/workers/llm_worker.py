# app/workers/llm_worker.py
import asyncio
import logging
from typing import Dict, Any
from ..aipipe_client import run_llm
from ..utils import run_with_timeout

logger = logging.getLogger("app.workers.llm_worker")


async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    LLM Worker: Use AiPipe (or fallback model) to read the instruction and produce an answer.
    """

    instruction = page_info.get("instruction") or page_info.get("text") or page_info.get("html", "")
    if not instruction:
        return {"worker": "llm", "error": "No instruction found"}

    prompt = (
        "You are a precise assistant. Read the instructions from the webpage and extract ONLY the exact answer.\n"
        "Do NOT add explanation. Do NOT rewrite the question.\n"
        "Return only the answer.\n\n"
        f"Instruction:\n{instruction}\n\nAnswer:"
    )

    try:
        answer = await run_llm(prompt)
        if answer:
            return {"worker": "llm", "answer": answer.strip()}
        return {"worker": "llm", "error": "Empty response from LLM"}
    except Exception as e:
        logger.exception("LLM worker error")
        return {"worker": "llm", "error": str(e)}
