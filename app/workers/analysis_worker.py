from typing import Dict, Any
import numpy as np, pandas as pd
from ..utils import logger

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Lightweight analysis worker: if data available, compute basic stats.
    """
    # reuse data_processing to get a df if data_url present
    from .data_processing_worker import handle as dp_handle
    res = await dp_handle(page_info, payload, deadline_ts)
    if "answer" in res:
        # direct numeric answer already computed
        return res
    # else respond with analysis summary
    return {"worker": "analysis", "note": "analysis worker currently delegates to data processing for basic tasks", "detail": res}
