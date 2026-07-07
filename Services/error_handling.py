from Database.database import (
    update_order_lifecycle,
    increment_retry,
)

from Services.logger import logger


def handle_order_error(
    *,
    db_id: int,
    error: Exception,
    retry: bool = False,
    max_retries: int = 3,
    current_retry: int = 0,
) -> None:
    """
    Handles processing errors for an order.

    Responsibilities:
    - Log the exception.
    - Increment retry count (optional).
    - Update lifecycle status.
    - Store failure reason.
    """

    error_message = str(error)

    logger.exception(
        f"Order {db_id} failed: {error_message}"
    )

    if retry and current_retry < max_retries:

        increment_retry(db_id)

        update_order_lifecycle(
            db_id,
            status="RETRY_PENDING",
            failure_reason=error_message,
        )

        logger.warning(
            f"Order {db_id} moved to RETRY_PENDING "
            f"({current_retry + 1}/{max_retries})"
        )

    else:

        update_order_lifecycle(
            db_id,
            status="FAILED",
            failure_reason=error_message,
        )

        logger.error(
            f"Order {db_id} marked FAILED."
        )


def handle_tracking_error(
    *,
    filename: str,
    error: Exception,
) -> None:
    """
    Handles failures while processing
    warehouse tracking files.
    """

    logger.exception(
        f"Tracking file '{filename}' failed: {error}"
    )


def handle_system_error(
    *,
    component: str,
    error: Exception,
) -> None:
    """
    Handles infrastructure-level failures.

    Examples:
    - Database unavailable
    - SFTP unavailable
    - Shopify unavailable
    """

    logger.critical(
        f"{component} failure: {error}",
        exc_info=True,
    )