import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from .schemas import QuizRequest
from .config import SECRET
from .worker import orchestrator_start
from .utils import logger

app = FastAPI(title="Quiz Solver Endpoint")

@app.get("/")
def root():
    return {"status": "running", "message": "LLM Quiz Solver API online"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/quiz")
async def receive_quiz(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        req = QuizRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    # secret validation
    if req.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # accepted — start orchestrator in background and return 200 immediately
    logger.info("Received quiz request for url=%s email=%s", req.url, req.email)
    # spawn background task
    asyncio.create_task(orchestrator_start(req.dict()))
    return JSONResponse(status_code=200, content={"status": "accepted", "note": "processing started"})
