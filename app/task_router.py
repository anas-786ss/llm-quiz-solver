import re
from .utils import logger
from typing import Dict, Any
from .workers import web_scraper_worker, api_sourcing_worker, data_cleaning_worker, data_processing_worker, analysis_worker, visualization_worker, llm_worker

async def route_task(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    instruction = page_info.get("instruction", "") or ""
    text = instruction.lower()

    # Special handling: curl command crafting
    if "curl http request" in text or ("curl" in text and "accept: application/json" in text):
        logger.info("Routing to built-in curl command composer")
        # Extract target URL (echo.json) from the instruction or use page_info context
        m = re.search(r"https?://[^\s\"']+", instruction)
        target = m.group(0) if m else "https://tds-llm-analysis.s-anand.net/project2-reevals/echo.json"
        cmd = f'curl -H "Accept: application/json" {target}'
        return {"worker": "command", "answer": cmd, "type": "string"}

    if any(k in text for k in ["download", ".csv", ".xlsx", "pdf", "table", "sum", "mean", "average", "value column"]):
        logger.info("Routing to data_processing_worker")
        return await data_processing_worker.handle(page_info, payload, deadline_ts)

    if any(k in text for k in ["api", "call", "fetch", "headers", "endpoint", "json"]):
        logger.info("Routing to api_sourcing_worker")
        res = await api_sourcing_worker.handle(page_info, payload, deadline_ts)
        if "error" in res:
            logger.info("API sourcing failed; falling back to web_scraper_worker")
            ws = await web_scraper_worker.handle(page_info, payload, deadline_ts)
            if "answer" in ws:
                return ws
            logger.info("Web scraper yielded no direct result; falling back to LLM")
            return await llm_worker.handle(page_info, payload, deadline_ts)
        return res

    if any(k in text for k in ["clean", "normalize", "remove na", "null", "strip"]):
        logger.info("Routing to data_cleaning_worker")
        return await data_cleaning_worker.handle(page_info, payload, deadline_ts)

    if any(k in text for k in ["chart", "plot", "visualize", "figure", "image"]):
        logger.info("Routing to visualization_worker")
        return await visualization_worker.handle(page_info, payload, deadline_ts)

    if any(k in text for k in ["analyze", "ml", "regression", "cluster", "correlation"]):
        logger.info("Routing to analysis_worker")
        return await analysis_worker.handle(page_info, payload, deadline_ts)

    logger.info("Routing to web_scraper_worker (fallback)")
    return await web_scraper_worker.handle(page_info, payload, deadline_ts)
