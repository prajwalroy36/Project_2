# Workers/sender_worker.py
import asyncio
from Services.Order_processor import process_engine_worker
from Core.config import settings
from Services.logger import logger  # Added the missing logger import

async def autonomous_sending_loop():
    """
    Runs continuously in the background to process pending orders.
    Delegates to a thread so it doesn't block the FastAPI web server.
    """
    logger.info("Autonomous sending loop started.")
    
    while True:
        try:
            # We must run this in a thread so it doesn't block FastAPI
            await asyncio.to_thread(process_engine_worker)
        except Exception as e:
            # If the database goes down or something critical fails, catch it and keep the loop alive
            logger.error(f"Critical failure in autonomous_sending_loop: {e}")
        
        # Fixed the setting name (was POLL_INTERVAL, should be WORKER_SLEEP_SECONDS)
        await asyncio.sleep(settings.WORKER_SLEEP_SECONDS)