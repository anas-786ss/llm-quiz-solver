from typing import Dict, Any
from ..aipipe_client import ask_openai
from ..utils import logger

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Use AiPipe LLM to parse instruction or summarise a PDF/text and provide an answer.
    This is a fallback and should be used when other workers can't handle the task.
    """
    instruction = page_info.get("instruction", "")
    prompt = f"""You are an assistant that reads this quiz instruction and returns a JSON with keys:
- action: one-line intent
- answer: computed answer if possible (number, string, boolean, or base64 image uri)
- explanation: short reasoning

Instruction:
{instruction}
"""
    resp = await ask_openai(prompt, model="openai/gpt-4.1-nano", timeout=25)
    if not resp:
        return {"worker": "llm", "error": "AiPipe not available or returned no response"}
    # Attempt to parse the response
    # The OpenRouter response shape may vary; try to get text
    text = None
    if isinstance(resp, dict):
        # attempt to extract a text field
        text = str(resp)
    else:
        text = str(resp)
    return {"worker": "llm", "response_raw": resp, "parsed_text": text[:4000]}
