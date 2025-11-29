import asyncio, re, base64, logging
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from ..utils import logger

async def render_page_extract(url: str, wait_until="networkidle", timeout=30000):
    """
    Launch playwright, navigate to url, wait for JS to render, and attempt to extract:
    - full text
    - any base64 embedded JSON (via atob calls)
    - submit URL (heuristic)
    - downloadable links (.csv, .xlsx, .pdf, images)
    Returns dict with keys: instruction, submit_url, data_urls, html
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
        except PWTimeout:
            logger.warning("Page load timeout, trying again with longer timeout")
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout*2)
        # wait small extra time for dynamic content
        await asyncio.sleep(1.0)
        html = await page.content()
        # heuristic: look for base64 through atob( `...` )
        script_texts = await page.eval_on_selector_all("script", "elements => elements.map(e => e.innerText)")
        combined = "\n".join([s for s in script_texts if s])
        instruction = ""
        # attempt to extract base64 chunks (common pattern from sample)
        b64_matches = re.findall(r"atob\(`([^`]+)`\)", combined)
        if b64_matches:
            try:
                dec = "".join([base64.b64decode(x).decode("utf-8", errors="ignore") for x in b64_matches])
                instruction = dec
            except Exception as e:
                logger.warning("Failed to decode base64: %s", e)
        # fallback: visible text
        if not instruction:
            visible = await page.inner_text("body")
            instruction = visible[:10000]
        # submit URL heuristic: look for /submit or submit endpoints in html
        submit_urls = re.findall(r"https?://[A-Za-z0-9./?=_-]*submit[A-Za-z0-9./?=_-]*", html)
        if not submit_urls:
            # look for forms with action
            try:
                form_action = await page.eval_on_selector("form", "f => f.action", timeout=2000)
                if form_action:
                    submit_urls = [form_action]
            except Exception:
                submit_urls = []
        data_urls = re.findall(r"https?://[A-Za-z0-9./?=_-]+\.(?:csv|xlsx|xls|pdf|png|jpg|jpeg)", html)
        # include links from anchors
        anchors = await page.query_selector_all("a")
        for a in anchors:
            try:
                href = await a.get_attribute("href")
                if href and href.startswith("http"):
                    if any(href.lower().endswith(ext) for ext in [".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"]):
                        data_urls.append(href)
            except Exception:
                pass
        await browser.close()
        return {
            "instruction": instruction,
            "submit_url": submit_urls[0] if submit_urls else None,
            "data_urls": list(dict.fromkeys(data_urls)),
            "html": html,
            "url": url
        }
