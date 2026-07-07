# Workers/tracking_worker.py
import asyncio

from Core.config import settings
from Database.database import get_order_by_order_id, update_order_lifecycle
from Services.error_handling import handle_tracking_error
from Services.logger import logger
from Services.tracking import cleanup_tracking_file, process_tracking


def process_tracking_worker() -> None:
    logger.info("Tracking worker started.")

    processed_files = process_tracking()
    if not processed_files:
        logger.info("No tracking files found.")
        return

    for file_data in processed_files:
        file = file_data["file"]
        records = file_data["records"]

        logger.info("Processing %s (%s records)", file["filename"], len(records))

        try:
            for record in records:
                order = get_order_by_order_id(record["order_id"])
                if order is None:
                    logger.warning("Order %s not found.", record["order_id"])
                    continue

                update_order_lifecycle(
                    order["db_id"],
                    status="COMPLETED",
                    tracking_number=record["tracking_number"],
                    carrier=record["carrier"],
                    tracking_received=True,
                    completed=True,
                )
                logger.info("Tracking updated for %s", record["order_id"])

            cleanup_tracking_file(file["local_path"], file["remote_path"])
            logger.info("%s processed successfully.", file["filename"])

        except Exception as exc:
            handle_tracking_error(filename=file["filename"], error=exc)

    logger.info("Tracking worker finished.")


async def autonomous_tracking_loop():
    logger.info("Autonomous tracking loop started.")

    while True:
        try:
            await asyncio.to_thread(process_tracking_worker)
        except Exception as exc:
            logger.error("Critical failure in tracking loop: %s", exc)

        await asyncio.sleep(settings.TRACKING_POLL_INTERVAL)
