# main.py
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager # ADDED: Required for lifespan
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from Workers.sender_worker import autonomous_sending_loop
from Workers.tracking_worker import autonomous_tracking_loop
from API.Webhook import router as webhook_router
from API.Dashboard import router as dashboard_router
from Core.config import settings

DEBUG_LOG_PATH = Path("debug-6ba292.log")

def _write_debug_log(payload: dict) -> None:
    payload.setdefault("sessionId", "6ba292")
    payload.setdefault("timestamp", int(time.time() * 1000))
    payload.setdefault("id", f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}")
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")

# 1. Define the Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # Start BOTH background processors independently when server boots
    asyncio.create_task(autonomous_sending_loop())
    asyncio.create_task(autonomous_tracking_loop())
    
    yield # This tells FastAPI to yield control and run the web application
    
    # --- SHUTDOWN LOGIC ---
    # (If you ever need to close database pools cleanly, you put it here)


# 2. Inject the lifespan into the FastAPI initialization
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# --- SECURITY: CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(webhook_router)
app.include_router(dashboard_router)

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        raw_body_bytes = await request.body()
        raw_body_text = raw_body_bytes.decode("utf-8", errors="ignore")
    except Exception:
        raw_body_text = "<unable_to_read_body>"

    # #region agent log
    _write_debug_log({
        "runId": "pre-fix",
        "hypothesisId": "H1-H4",
        "location": "main.py:request_validation_exception_handler",
        "message": "FastAPI request validation failed",
        "data": {
            "path": str(request.url.path),
            "method": request.method,
            "contentType": request.headers.get("content-type"),
            "errors": exc.errors(),
            "bodyPreview": raw_body_text[:1200],
        },
    })
    # #endregion

    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.get("/")
def health():
    return {"status": "running", "environment": settings.ENVIRONMENT}
   