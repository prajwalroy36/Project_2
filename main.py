# main.py
import asyncio
from contextlib import asynccontextmanager # ADDED: Required for lifespan
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Workers.sender_worker import autonomous_sending_loop
from Workers.tracking_worker import autonomous_tracking_loop
from API.Webhook import router as webhook_router
from API.Dashboard import router as dashboard_router
from Core.config import settings

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

@app.get("/")
def health():
    return {"status": "running", "environment": settings.ENVIRONMENT}
   