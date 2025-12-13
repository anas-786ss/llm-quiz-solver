import asyncio, re, base64, logging
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from ..utils import logger

# ... keep imports ...

async def render_page_extract(url: str, wait_until="networkidle", timeout=30000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
        except PWTimeout:
            logger.warning("Page load timeout, trying again with longer timeout")
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout*2)
        await asyncio.sleep(1.0)
        html = await page.content()
        script_texts = await page.eval_on_selector_all("script", "elements => elements.map(e => e.innerText)")
        combined = "\n".join([s for s in script_texts if s])
        instruction = ""
        b64_matches = re.findall(r"atob\(`([^`]+)`\)", combined)
        if b64_matches:
            try:
                dec = "".join([base64.b64decode(x).decode("utf-8", errors="ignore") for x in b64_matches])
                instruction = dec
            except Exception as e:
                logger.warning("Failed to decode base64: %s", e)
        if not instruction:
            visible = await page.inner_text("body")
            instruction = visible[:10000]
        submit_urls = re.findall(r"https?://[A-Za-z0-9./?=_-]*submit[A-Za-z0-9./?=_-]*", html)
        if not submit_urls:
            try:
                visible = await page.inner_text("body")
            except Exception:
                visible = ""
            if "/submit" in html or "/submit" in visible:
                try:
                    origin = await page.evaluate("() => window.location.origin")
                    if origin:
                        submit_urls = [origin.rstrip("/") + "/submit"]
                except Exception:
                    pass
        if not submit_urls:
            try:
                form_action = await page.eval_on_selector("form", "f => f.action", timeout=2000)
                if form_action:
                    submit_urls = [form_action]
            except Exception:
                submit_urls = []
        data_urls = re.findall(r"https?://[A-Za-z0-9./?=_-]+\.(?:csv|xlsx|xls|pdf|png|jpg|jpeg)", html)
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
