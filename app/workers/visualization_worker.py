import matplotlib.pyplot as plt
import io, base64, pandas as pd
from typing import Dict, Any
from ..utils import logger
from ..browser.downloader import download_file
import tempfile, os

async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Create a basic plot for first numeric column and return base64 image URI.
    """
    data_urls = page_info.get("data_urls", [])
    if not data_urls:
        return {"worker": "visualization", "error": "no data url"}
    url = data_urls[0]
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    dest = tmp.name
    try:
        await download_file(url, dest)
        if url.lower().endswith(".csv"):
            df = pd.read_csv(dest)
        else:
            return {"worker": "visualization", "error": "unsupported format"}
        numerics = df.select_dtypes(include="number").columns
        if len(numerics) == 0:
            return {"worker":"visualization","error":"no numeric columns"}
        col = numerics[0]
        plt.figure(figsize=(6,3))
        df[col].plot(kind="line")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("ascii")
        uri = f"data:image/png;base64,{b64}"
        return {"worker":"visualization","image":uri, "type":"image"}
    finally:
        try:
            os.remove(dest)
        except Exception:
            pass
