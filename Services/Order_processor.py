# Services/Order_processor.py
import os

from Core.config import settings
from Core.constrain import (
    PROCESSING,
    TRANSFORMED,
    CSV_GENERATED,
    UPLOADED,
    AWAITING_TRACKING,
    RETRY_PENDING,
    HELD_FOR_REVIEW,
)

from Database.database import (
    get_next_pending_order,
    update_order_lifecycle,
    increment_retry,
)

from Services.transformers import transform_order
from Services.csv_generator import generate_csv
from Services.warehouse import upload_via_sftp
from Services.alerts import send_critical_alert

from Services.logger import (
    log_order_event,
    
)

from Services.error_handling import handle_order_error


def process_engine_worker() -> None:
    """
    Main processing engine.

    One execution processes one order.

    Lifecycle:

    Pending
        ↓
    Processing
        ↓
    Transform
        ↓
    CSV
        ↓
    Upload
        ↓
    Await Tracking
    """

    order = get_next_pending_order()

    if order is None:
        return

    db_id = order["db_id"]
    order_id = order["order_id"]
    raw_payload = order["raw_payload"]
    retry_count = order["retry_count"]

    csv_file = None

    log_order_event(
        order_id=order_id,
        db_id=db_id,
        stage="PROCESSOR",
        status="STARTED",
        message="Order processing started.",
    )

    try:

        # --------------------------------------------------
        # PROCESSING
        # --------------------------------------------------

        update_order_lifecycle(
            db_id,
            status=PROCESSING,
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="PROCESSING",
            status="SUCCESS",
            message="Lifecycle updated.",
        )

        # --------------------------------------------------
        # TRANSFORM
        # --------------------------------------------------

        warehouse_payload = transform_order(raw_payload)

        update_order_lifecycle(
            db_id,
            status=TRANSFORMED,
            warehouse_payload=warehouse_payload,
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="TRANSFORM",
            status="SUCCESS",
            message="Order transformed.",
        )

        # --------------------------------------------------
        # CSV
        # --------------------------------------------------

        csv_file = generate_csv(warehouse_payload)

        update_order_lifecycle(
            db_id,
            status=CSV_GENERATED,
            csv_filename=csv_file,
            csv_generated=True,
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="CSV",
            status="SUCCESS",
            message="Warehouse CSV generated.",
        )

        # --------------------------------------------------
        # UPLOAD
        # --------------------------------------------------

        remote_filename = upload_via_sftp(csv_file)

        update_order_lifecycle(
            db_id,
            status=UPLOADED,
            warehouse_filename=remote_filename,
            uploaded=True,
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="UPLOAD",
            status="SUCCESS",
            message="CSV uploaded to warehouse.",
        )

        # --------------------------------------------------
        # WAITING FOR TRACKING
        # --------------------------------------------------

        update_order_lifecycle(
            db_id,
            status=AWAITING_TRACKING,
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="PROCESSOR",
            status="COMPLETED",
            message="Order processing finished successfully.",
        )

        log_order_event(
            order_id=order_id,
            db_id=db_id,
            stage="TRACKING",
            status="WAITING",
            message="Waiting for warehouse tracking.",
        )

    except Exception as error:
        # ALL of this must be indented inside the except block
        handle_order_error(
            db_id=db_id,
            error=error,
        )

        if retry_count < settings.MAX_RETRIES:
            increment_retry(db_id)
            update_order_lifecycle(
                db_id,
                status=RETRY_PENDING,
                failure_reason=str(error),
            )
            log_order_event(
                order_id=order_id,
                db_id=db_id,
                stage="RETRY",
                status="SCHEDULED",
                message=(
                    f"Retry {retry_count + 1} of "
                    f"{settings.MAX_RETRIES} scheduled."
                ),
            )
        else:
            update_order_lifecycle(
                db_id,
                status=HELD_FOR_REVIEW,
                failure_reason=str(error),
            )
            send_critical_alert(
                str(order_id),
                str(error),
            )
            log_order_event(
                order_id=order_id,
                db_id=db_id,
                stage="REVIEW",
                status="HELD",
                message="Maximum retry attempts exceeded.",
            )
    
    finally:
        # Clean up the local CSV file so the server doesn't run out of storage
        if csv_file and os.path.exists(csv_file):
            try:
                os.remove(csv_file)
                log_order_event(
                    order_id=order_id,
                    db_id=db_id,
                    stage="CLEANUP",
                    status="SUCCESS",
                    message="Local CSV deleted."
                )
            except Exception as cleanup_error:
                # Log cleanup errors without crashing the main process
                handle_order_error(
                    db_id=db_id,
                    error=cleanup_error,
                )