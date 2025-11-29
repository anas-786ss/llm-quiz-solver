import pandas as pd, numpy as np
from typing import Dict, Any
from ..utils import logger

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Receive a DataFrame-like instruction or CSV URL in page_info; perform cleaning per heuristics.
    For demo: if CSV present, remove nulls and return row count.
    """
    # delegate to web_scraper to download or re-use page_info data_urls
    data_urls = page_info.get("data_urls", [])
    if not data_urls:
        return {"worker": "data_cleaning", "error": "no data url present"}
    import tempfile, os
    from ..browser.downloader import download_file
    url = data_urls[0]
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    dest = tmp.name
    try:
        await download_file(url, dest)
        if url.lower().endswith(".csv"):
            df = pd.read_csv(dest)
        else:
            return {"worker": "data_cleaning", "error": "unsupported format"}
        # basic cleaning
        df = df.dropna(how="all")
        # strip whitespace from string columns
        for c in df.select_dtypes(include="object").columns:
            df[c] = df[c].astype(str).str.strip()
        return {"worker": "data_cleaning", "rows": int(len(df)), "columns": list(df.columns)}
    finally:
        try:
            os.remove(dest)
        except Exception:
            pass
