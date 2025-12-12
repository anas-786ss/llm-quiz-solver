import pandas as pd
import os, tempfile, re
from typing import Dict, Any
from ..utils import logger
from ..browser.downloader import download_file
import PyPDF2

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
    Data processing: download CSV/XLSX and perform simple transformations described in instruction.
    Common tasks: sum column, filter rows, pivot.
    This is a pragmatic implementation to cover the common quiz types.
    """
    data_urls = page_info.get("data_urls", [])
    instruction = page_info.get("instruction", "").lower()
    if not data_urls:
        # try reading tables from html handled elsewhere
        return {"worker": "data_processing", "error": "no data URL present"}
    file_url = data_urls[0]
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    dest = tmp.name
    try:
        await download_file(file_url, dest)
        
        # Check for PDF with page-specific extraction
        page_match = re.search(r'page\s+(\d+)', instruction)
        if page_match and file_url.lower().endswith('.pdf'):
            page_num = int(page_match.group(1))
            # Extract from that specific page
            pdf_text = await extract_pdf_text(dest, page_num=page_num)
            return {"worker": "data_processing", "note": f"PDF page {page_num} extracted; handing to LLM worker", "pdf_text": pdf_text, "fallback_to": "llm"}
        
        if file_url.lower().endswith(".csv"):
            df = pd.read_csv(dest)
        elif file_url.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(dest)
        elif file_url.lower().endswith(".pdf"):
            # PDF without specific page -> extract all and fallback to LLM
            pdf_text = await extract_pdf_text(dest)
            return {"worker": "data_processing", "note": "PDF file; handing to LLM worker", "pdf_text": pdf_text, "fallback_to": "llm"}
        else:
            return {"worker": "data_processing", "error": "unsupported file type for automatic processing"}
        # if instruction asks for sum of "value"
        if "sum" in instruction and "value" in instruction:
            # find candidate column
            col = None
            for c in df.columns:
                if "value" in str(c).lower():
                    col = c
                    break
            if col is None:
                numerics = df.select_dtypes(include="number").columns
                col = numerics[0] if len(numerics) else None
            if col is None:
                return {"worker": "data_processing", "error": "no numeric column found"}
            val = df[col].sum()
            return {"worker": "data_processing", "answer": int(val), "type": "number"}
        # default: return rows and columns
        return {"worker": "data_processing", "rows": int(len(df)), "columns": list(df.columns)}
    finally:
        try:
            os.remove(dest)
        except Exception:
            pass
