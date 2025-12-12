import asyncio, logging
from ..utils import logger
from typing import Dict, Any
from ..browser.downloader import download_file
import pandas as pd
import os, tempfile
import PyPDF2
import io

async def extract_pdf_text(file_path: str, page_num: int = None) -> str:
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


async def handle(page_info: Dict[str, Any], payload: Dict[str, Any], deadline_ts: float) -> Dict[str, Any]:
    """
    Extract table-like data from the rendered page HTML (simple heuristics).
    """
    instruction = page_info.get("instruction", "")
    url = page_info.get("url")
    html = page_info.get("html", "")
    # attempt to find CSV/links
    data_urls = page_info.get("data_urls", [])
    # if CSV found, download and compute a naive result
    if data_urls:
        # use first CSV/XLSX/PDF
        file_url = data_urls[0]
        tmp = tempfile.NamedTemporaryFile(delete=False)
        dest = tmp.name
        tmp.close()
        await download_file(file_url, dest)
        try:
            if file_url.lower().endswith(".csv"):
                df = pd.read_csv(dest)
            elif file_url.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(dest)
            else:
                # PDF / images -> fallback to returning instruction to LLM worker
                return {"worker": "web_scraper", "note": "non-tabular file; handing to LLM worker", "fallback_to": "llm"}
            # simple aggregate: if instruction asks "sum of value column" attempt to find column name
            # naive: look for column named 'value' or 'Value' or numeric columns
            col = None
            for c in df.columns:
                if "value" in str(c).lower():
                    col = c
                    break
            if col is None:
                # pick numeric column with most non-null
                numerics = df.select_dtypes(include="number").columns
                col = list(numerics)[0] if len(numerics) else None
            if col is None:
                return {"worker": "web_scraper", "error": "no numeric column found"}
            result = df[col].sum()
            return {"worker": "web_scraper", "answer": result, "type": "number"}
        finally:
            try:
                os.remove(dest)
            except Exception:
                pass
    # fallback: parse HTML tables
    try:
        tables = pd.read_html(html)
        if len(tables) > 0:
            df = tables[0]
            numerics = df.select_dtypes(include="number").columns
            col = numerics[0] if len(numerics) else None
            if col is None:
                return {"worker": "web_scraper", "error": "no numeric column in html table"}
            return {"worker": "web_scraper", "answer": int(df[col].sum()), "type": "number"}
    except Exception as e:
        logger.warning("pd.read_html failed: %s", e)
    # fallback to LLM
    return {"worker": "web_scraper", "note": "no direct table found", "fallback_to": "llm"}
