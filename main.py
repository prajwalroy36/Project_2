from fastapi import FastAPI
from Workers.sender_worker import autonomous_sending_loop
import asyncio
from API.Webhook import router as webhook_router

app = FastAPI()

app.include_router(webhook_router)

@app.get("/")
def health():
    return {
        "status": "running"
    }

@app.on_event("startup")
async def startup_event():

    asyncio.create_task(autonomous_sending_loop())
   