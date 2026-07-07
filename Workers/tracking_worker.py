# Workers/tracking_worker.py
import asyncio
from Core.config import settings

from Database.database import (
    get_order_by_order_id,
    update_order_lifecycle,
)
from Services.error_handling import (
    handle_tracking_error,
)
from Services.logger import logger
from Services.tracking import (
    process_tracking,
    cleanup_tracking_file,
)


def process_tracking_worker() -> None:
    """
    Processes every downloaded warehouse tracking file
    and updates matching orders.
    """
    logger.info("Tracking worker started.")

    processed_files = process_tracking()

    if not processed_files:
        logger.info("No tracking files found.")
        return

    for file_data in processed_files:
        file = file_data["file"]
        records = file_data["records"]

        logger.info(
            f"Processing {file['filename']} "
            f"({len(records)} records)"
        )

        try:
            for record in records:
                order = get_order_by_order_id(
                    record["order_id"]
                )

                if order is None:
                    logger.warning(
                        f"Order {record['order_id']} not found."
                    )
                    continue

                update_order_lifecycle(
                    order["db_id"],
                    status="COMPLETED",
                    tracking_number=record["tracking_number"],
                    carrier=record["carrier"],
                    tracking_received=True,
                    completed=True,
                )

                logger.info(
                    f"Tracking updated for "
                    f"{record['order_id']}"
                )

            cleanup_tracking_file(
                file["local_path"],
                file["remote_path"],
            )

            logger.info(
                f"{file['filename']} processed successfully."
            )

        except Exception as e:
            handle_tracking_error(
                filename=file["filename"],
                error=e,
            )

    logger.info("Tracking worker finished.")


async def autonomous_tracking_loop():
    """
    Runs in the background, waking up periodically to check the warehouse
    SFTP for tracking CSVs, processing them, and going back to sleep.
    """
    while True:
        try:
            # We run the synchronous tracking worker inside an executor
            # so it doesn't block the FastAPI async event loop.
            await asyncio.to_thread(process_tracking_worker)
        except Exception as e:
            logger.error(f"Critical failure in tracking loop: {e}")
        
        # Check for tracking every 15 minutes (900 seconds)
        # You can add TRACKING_POLL_INTERVAL=900 to your .env
        await asyncio.sleep(getattr(settings, 'TRACKING_POLL_INTERVAL', 900))