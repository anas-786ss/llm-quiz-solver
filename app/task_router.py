import re, logging, asyncio
from .workers import web_scraper_worker, api_sourcing_worker, data_cleaning_worker, data_processing_worker, analysis_worker, visualization_worker, llm_worker
from .utils import logger
from typing import Dict, Any

# naive keyword-based router + fallback to LLM
async def route_task(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    instruction = page_info.get("instruction", "") or ""
    text = instruction.lower()
    # quick keyword checks
    if any(k in text for k in ["download", ".csv", ".xlsx", "pdf", "table", "sum", "mean", "average", "value column"]):
        # prefer data pipeline
        logger.info("Routing to data_processing_worker")
        return await data_processing_worker.handle(page_info, payload, deadline_ts)
    if "api" in text or "call" in text or "fetch" in text or "headers" in text:
        logger.info("Routing to api_sourcing_worker")
        return await api_sourcing_worker.handle(page_info, payload, deadline_ts)
    if any(k in text for k in ["clean", "normalize", "remove na", "null", "strip"]):
        logger.info("Routing to data_cleaning_worker")
        return await data_cleaning_worker.handle(page_info, payload, deadline_ts)
    if any(k in text for k in ["chart", "plot", "visualize", "figure", "image"]):
        logger.info("Routing to visualization_worker")
        return await visualization_worker.handle(page_info, payload, deadline_ts)
    if any(k in text for k in ["analyze", "ml", "regression", "cluster", "correlation"]):
        logger.info("Routing to analysis_worker")
        return await analysis_worker.handle(page_info, payload, deadline_ts)
    # fallback: try web scraping first
    logger.info("Routing to web_scraper_worker (fallback)")
    return await web_scraper_worker.handle(page_info, payload, deadline_ts)
