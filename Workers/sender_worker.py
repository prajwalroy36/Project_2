from Services.Order_processor import process_engine_worker
import asyncio
from Core.config import settings

# Workers/sender_worker.py

async def autonomous_sending_loop():

    while True:

        process_engine_worker()

        await asyncio.sleep(settings.POLL_INTERVAL)