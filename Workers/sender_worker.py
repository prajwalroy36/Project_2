# Workers/sender_worker.py
import asyncio

from Core.config import settings
from Services.logger import logger
from Services.metrics import evaluate_queue_health
from Services.Order_processor import process_engine_worker

_metrics_tick = 0
_METRICS_CHECK_EVERY = 12


async def autonomous_sending_loop():
    """
    Runs continuously in the background to process pending orders.
    """
    global _metrics_tick

    logger.info("Autonomous sending loop started.")

    while True:
        try:
            await asyncio.to_thread(process_engine_worker)

            _metrics_tick += 1
            if _metrics_tick >= _METRICS_CHECK_EVERY:
                _metrics_tick = 0
                health = await asyncio.to_thread(evaluate_queue_health)
                if not health["healthy"]:
                    logger.warning("Queue health alerts: %s", health["alerts"])

        except Exception as exc:
            logger.error("Critical failure in autonomous_sending_loop: %s", exc)

        await asyncio.sleep(settings.WORKER_SLEEP_SECONDS)
