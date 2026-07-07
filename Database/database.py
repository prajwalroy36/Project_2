import json
from datetime import date, datetime

from psycopg.types.json import Json

from Database.pool import get_connection
from Schemas.Order import OrderPayload


def _serialize_row_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def insert_order(order_id: str, raw_payload: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO queue(order_id, raw_payload, status, retry_count)
                VALUES(%s, %s::jsonb, %s, %s)
                """,
                (order_id, raw_payload, "PENDING", 0),
            )
        conn.commit()


def get_next_pending_order() -> dict | None:
    """
    Atomically claims the next pending order so workers cannot double-process.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE queue
                SET status = 'PROCESSING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id
                    FROM queue
                    WHERE status IN ('PENDING', 'RETRY_PENDING')
                    ORDER BY id ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, order_id, raw_payload, retry_count
                """
            )
            row = cursor.fetchone()
        conn.commit()

        if row is None:
            return None

        return {
            "db_id": row[0],
            "order_id": row[1],
            "raw_payload": row[2],
            "retry_count": row[3],
        }


def update_order_status(db_id: int, status: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE queue
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, db_id),
            )
        conn.commit()


def increment_retry(db_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE queue
                SET retry_count = retry_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (db_id,),
            )
        conn.commit()


def get_recent_orders(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, order_id, status, retry_count
                FROM queue
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()

    return [
        {
            "db_id": row[0],
            "order_id": row[1],
            "status": row[2],
            "retry_count": row[3],
        }
        for row in rows
    ]


def retry_held_order(db_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE queue
                SET status = 'RETRY_PENDING',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (db_id,),
            )
        conn.commit()


def update_order_lifecycle(
    db_id: int,
    *,
    status: str | None = None,
    warehouse_payload: dict | None = None,
    csv_filename: str | None = None,
    warehouse_filename: str | None = None,
    tracking_number: str | None = None,
    carrier: str | None = None,
    failure_reason: str | None = None,
    csv_generated: bool = False,
    uploaded: bool = False,
    tracking_received: bool = False,
    completed: bool = False,
) -> None:
    updates = []
    values = []

    if status is not None:
        updates.append("status=%s")
        values.append(status)

    if warehouse_payload is not None:
        updates.append("warehouse_payload=%s")
        values.append(Json(warehouse_payload))

    if csv_filename is not None:
        updates.append("csv_filename=%s")
        values.append(csv_filename)

    if warehouse_filename is not None:
        updates.append("warehouse_filename=%s")
        values.append(warehouse_filename)

    if tracking_number is not None:
        updates.append("tracking_number=%s")
        values.append(tracking_number)

    if carrier is not None:
        updates.append("carrier=%s")
        values.append(carrier)

    if failure_reason is not None:
        updates.append("failure_reason=%s")
        values.append(failure_reason)

    if csv_generated:
        updates.append("csv_generated_at=CURRENT_TIMESTAMP")

    if uploaded:
        updates.append("uploaded_at=CURRENT_TIMESTAMP")

    if tracking_received:
        updates.append("tracking_received_at=CURRENT_TIMESTAMP")

    if completed:
        updates.append("completed_at=CURRENT_TIMESTAMP")

    updates.append("updated_at=CURRENT_TIMESTAMP")
    values.append(db_id)

    query = f"""
        UPDATE queue
        SET {", ".join(updates)}
        WHERE id=%s
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values)
        conn.commit()


def get_order_by_order_id(order_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, order_id, status
                FROM queue
                WHERE order_id = %s
                LIMIT 1
                """,
                (order_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "db_id": row[0],
        "order_id": row[1],
        "status": row[2],
    }


def get_order_details(db_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, order_id, status, retry_count, failure_reason,
                       raw_payload, warehouse_payload,
                       created_at, updated_at, csv_generated_at,
                       uploaded_at, tracking_received_at, completed_at,
                       tracking_number, carrier
                FROM queue
                WHERE id = %s
                """,
                (db_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    def _parse_json(value):
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        return json.loads(value)

    return {
        "db_id": row[0],
        "order_id": row[1],
        "status": row[2],
        "retry_count": row[3],
        "failure_reason": row[4],
        "raw_payload": _parse_json(row[5]),
        "warehouse_payload": _parse_json(row[6]),
        "created_at": _serialize_row_value(row[7]),
        "updated_at": _serialize_row_value(row[8]),
        "csv_generated_at": _serialize_row_value(row[9]),
        "uploaded_at": _serialize_row_value(row[10]),
        "tracking_received_at": _serialize_row_value(row[11]),
        "completed_at": _serialize_row_value(row[12]),
        "tracking_number": row[13],
        "carrier": row[14],
    }


def update_order_payload(db_id: int, new_raw_payload: dict) -> None:
    validated = OrderPayload.model_validate(new_raw_payload)
    payload_json = validated.model_dump_json()

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE queue
                SET raw_payload = %s::jsonb,
                    status = 'PENDING',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (payload_json, db_id),
            )
        conn.commit()


def get_queue_metrics() -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed,
                    COUNT(*) FILTER (WHERE status = 'RETRY_PENDING') AS retry_pending,
                    COUNT(*) FILTER (WHERE status = 'HELD_FOR_REVIEW') AS held,
                    COUNT(*) FILTER (WHERE status IN ('PENDING', 'PROCESSING')) AS in_flight,
                    COUNT(*) FILTER (
                        WHERE status = 'COMPLETED'
                          AND created_at::date = CURRENT_DATE
                    ) AS completed_today,
                    COUNT(*) FILTER (
                        WHERE created_at::date = CURRENT_DATE
                    ) AS received_today
                FROM queue
                """
            )
            row = cursor.fetchone()

    total = row[0] or 0
    completed = row[1] or 0
    held = row[3] or 0

    return {
        "total_orders": total,
        "completed": completed,
        "retry_pending": row[2] or 0,
        "held_for_review": held,
        "in_flight": row[4] or 0,
        "completed_today": row[5] or 0,
        "received_today": row[6] or 0,
        "success_rate": round((completed / total) * 100, 2) if total else 100.0,
        "retry_rate": round(((row[2] or 0) / total) * 100, 2) if total else 0.0,
        "held_rate": round((held / total) * 100, 2) if total else 0.0,
    }
