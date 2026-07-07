# main.py
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from API.Dashboard import router as dashboard_router
from API.Webhook import router as webhook_router
from Core.config import settings
from Database.pool import check_db_connection, close_pool, init_pool
from Services.metrics import evaluate_queue_health
from Workers.sender_worker import autonomous_sending_loop
from Workers.tracking_worker import autonomous_tracking_loop

DEBUG_LOG_PATH = Path("debug-6ba292.log")


def _write_debug_log(payload: dict) -> None:
    payload.setdefault("sessionId", "6ba292")
    payload.setdefault("timestamp", int(time.time() * 1000))
    payload.setdefault("id", f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}")
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    sender_task = asyncio.create_task(autonomous_sending_loop())
    tracking_task = asyncio.create_task(autonomous_tracking_loop())

    yield

    sender_task.cancel()
    tracking_task.cancel()
    close_pool()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def root():
    return {"status": "running", "environment": settings.ENVIRONMENT}


@app.get("/health")
def health():
    db_ok = check_db_connection()
    queue_health = evaluate_queue_health() if db_ok else {"metrics": {}, "alerts": ["database_unreachable"], "healthy": False}

    return {
        "status": "healthy" if db_ok and queue_health["healthy"] else "degraded",
        "environment": settings.ENVIRONMENT,
        "database": "up" if db_ok else "down",
        "workers": {
            "sender": "running",
            "tracking": "running",
        },
        "queue": queue_health["metrics"],
        "alerts": queue_health["alerts"],
        "security": {
            "webhook_hmac_required": settings.WEBHOOK_HMAC_REQUIRED,
            "dashboard_api_key_required": True,
        },
    }
