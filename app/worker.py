import asyncio, time, traceback, json
from .utils import logger, run_with_timeout, now_ts, submit_answer
from .browser.browser_runner import render_page_extract
from .task_router import route_task
from .config import GLOBAL_TIMEOUT, EMAIL
from typing import Dict, Any

async def orchestrator_start(payload: Dict[str, Any]):
    start_ts = now_ts()
    deadline = start_ts + GLOBAL_TIMEOUT
    try:
        logger.info("Orchestrator started for %s", payload.get("url"))
        page_info = await run_with_timeout(render_page_extract(payload.get("url")), GLOBAL_TIMEOUT, name="render_page")
        current_url = payload.get("url")
        submit_url = page_info.get("submit_url")
        # main loop: route -> compute -> submit -> possibly follow next url
        attempts = 0
        last_result = None
        while True:
            attempts += 1
            # route and compute
            res = await route_task(page_info, payload, deadline)
            last_result = res
            # prepare submission if answer present
            answer = res.get("answer")
            if answer is not None and submit_url:
                submit_payload = {
                    "email": payload.get("email"),
                    "secret": payload.get("secret"),
                    "url": current_url,
                    "answer": answer
                }
                try:
                    logger.info("Submitting answer to %s payload keys=%s", submit_url, list(submit_payload.keys()))
                    resp = await submit_answer(submit_url, submit_payload, timeout=15)
                    logger.info("Submit response: %s", resp)
                except Exception as e:
                    logger.error("Submission failed: %s", e)
                    resp = {"error": str(e)}
                # check response for correctness and next url
                if isinstance(resp, dict):
                    if resp.get("correct") is True:
                        # move to next url if provided
                        next_url = resp.get("url")
                        if next_url:
                            logger.info("Received next url: %s", next_url)
                            current_url = next_url
                            # load next page
                            page_info = await run_with_timeout(render_page_extract(current_url), 40, name="render_next_page")
                            submit_url = page_info.get("submit_url")
                            continue
                        else:
                            logger.info("Quiz finished (no next url).")
                            break
                    else:
                        # incorrect answer; if next url present, follow; otherwise allow a reattempt if time remains
                        next_url = resp.get("url")
                        if next_url:
                            current_url = next_url
                            page_info = await run_with_timeout(render_page_extract(current_url), 40, name="render_next_page")
                            submit_url = page_info.get("submit_url")
                            continue
                        else:
                            # allow at most one reattempt if time remains
                            if now_ts() + 10 < deadline and attempts < 3:
                                logger.info("Re-attempting solution for same URL (attempt %d)", attempts+1)
                                # small delay and try again (call route_task again)
                                await asyncio.sleep(1)
                                continue
                            else:
                                logger.info("No more attempts left or out of time.")
                                break
                else:
                    logger.info("Submit didn't return JSON.")
                    break
            else:
                # no direct answer: maybe the worker returned fallback instructions or produced an image
                if res.get("fallback_to") == "llm":
                    # call LLM worker explicitly
                    logger.info("Fallback to LLM worker")
                # If worker produced image data or other artifact and submit_url exists, try to send
                if res.get("type") == "image" and submit_url:
                    submit_payload = {
                        "email": payload.get("email"),
                        "secret": payload.get("secret"),
                        "url": current_url,
                        "answer": res.get("image")
                    }
                    try:
                        resp = await submit_answer(submit_url, submit_payload, timeout=15)
                        logger.info("Submitted image response: %s", resp)
                    except Exception as e:
                        logger.error("Image submission failed: %s", e)
                else:
                    logger.info("No answer produced by worker; stopping.")
                    break
            # check timeout
            if now_ts() > deadline:
                logger.warning("Global deadline reached; stopping handler")
                break
    except Exception as e:
        logger.error("Orchestrator error: %s", e)
        traceback.print_exc()
    finally:
        logger.info("Orchestrator finished for %s", payload.get("url"))
