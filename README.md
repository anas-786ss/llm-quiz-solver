# llm_quiz_solver

Local development and run instructions for the Quiz Solver endpoint.

Requirements
- Python 3.11 (recommended) — a venv is provided in `.venv311` if you followed the automated setup.
- Playwright Python package is required; Playwright browser binaries are optional for quick testing.

Quick start (Windows PowerShell)

1. Activate the prepared venv:

```powershell
.\.venv311\Scripts\Activate
```

2. (Optional) Install Playwright browser binaries. Installing all browsers can take a while; install only Chromium for faster setup:

```powershell
# install only Chromium
python -m playwright install chromium

# or install all three engines (chromium, firefox, webkit)
python -m playwright install
```

3. Run the API server with uvicorn:

```powershell
uvicorn app.main:app --reload
```

4. Test the endpoint using the included test script `scripts/test_local_submission.py` (this sends the demo payload to your local server):

```powershell
python scripts/test_local_submission.py
```

Troubleshooting
- If Playwright browser installation hangs or is slow, install only the engine you need (chromium) as shown above.
- If the background worker submits answers to remote demo servers, watch the server logs for progress — the endpoint returns immediately (HTTP 200) and processing happens in background.

Notes about the implementation
- The `/quiz` endpoint validates JSON and the provided `SECRET` environment variable. It returns HTTP 400 for invalid JSON/payload and 403 for invalid secret.
- A background orchestrator uses Playwright (headless) to render the quiz page, heuristically extract a submit URL and any attached data files, route the task to a worker, compute an answer, and submit it to the quiz submit endpoint within the configured timeout.
- The repository contains simple workers for common quiz types (scraping tables, downloading files, simple aggregations, visualization, and an LLM fallback).

If you want me to run the smoke test here (launch Chromium and fetch https://example.com), say so and I will run it and show the output.
