import psycopg
from Core.config import settings
from psycopg.types.json import Json


DATABASE_URL = settings.DATABASE_URL

def get_connection():
    
    return psycopg.connect(DATABASE_URL)

# Database/database.py

def insert_order(order_id: str, raw_payload: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # REPAIR: Added ::jsonb to explicitly cast the string for Postgres
            cursor.execute("""
                INSERT INTO queue(order_id, raw_payload, status, retry_count)
                VALUES(%s, %s::jsonb, %s, %s)
            """, (order_id, raw_payload, "PENDING", 0))
        conn.commit()
    finally:
        conn.close()

def get_next_pending_order() -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # REPAIR: Added FOR UPDATE SKIP LOCKED to prevent duplicate processing
            cursor.execute("""
                SELECT id, order_id, raw_payload, retry_count
                FROM queue 
                WHERE STATUS IN ('PENDING', 'RETRY_PENDING')
                ORDER BY id ASC 
                LIMIT 1 
                FOR UPDATE SKIP LOCKED
            """)
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return {
                "db_id": row[0],
                "order_id": row[1],
                "raw_payload": row[2],
                "retry_count": row[3]
            }
    finally:
        conn.close()

def update_order_status(db_id:int, status:str)-> None:

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                            UPDATE queue
                            SET status = %s
                            WHERE id = %s""",
                            (status,db_id))

            conn.commit()
    finally:
        conn.close()  

def increment_retry(db_id:int): 

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                           UPDATE queue
                           SET retry_count = retry_count + 1
                           WHERE id = %s""",
                           (db_id,))

            conn.commit()
    finally:
        conn.close()   

def get_recent_orders(limit : int = 100)-> list[dict]:

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT id, order_id, status, retry_count FROM queue
                           ORDER BY  id DESC
                           LIMIT %s""",
                           (limit,)) 
            
            rows = cursor.fetchall()

            orders = []

            for row in rows:

                order = {
                    "db_id": row[0],
                    "order_id":row[1],
                    "status":row[2],
                    "retry_count":row[3]

                }

                orders.append(order)

            return orders
    finally:
        conn.close()

def retry_held_order(db_id: int) -> None:

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE queue
                SET
                    status = 'RETRY_PENDING',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (db_id,))

        conn.commit()

    finally:
        conn.close()




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
):

    conn = get_connection()

    try:

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

        with conn.cursor() as cursor:
            cursor.execute(query, values)

        conn.commit()

    finally:
        conn.close()

def get_order_by_order_id(order_id: str) -> dict | None:
    """
    Returns the database row for a given Shopify order ID.
    """

    conn = get_connection()

    try:
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

    finally:
        conn.close()

import json

def get_order_details(db_id: int) -> dict | None:
    """Fetches the full lifecycle and payload details of a specific order for the frontend UI."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, order_id, status, retry_count, failure_reason, 
                       raw_payload, warehouse_payload, 
                       created_at, updated_at
                FROM queue
                WHERE id = %s
            """, (db_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            
            return {
                "db_id": row[0],
                "order_id": row[1],
                "status": row[2],
                "retry_count": row[3],
                "failure_reason": row[4],
                "raw_payload": row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}"),
                "warehouse_payload": row[6] if isinstance(row[6], dict) else json.loads(row[6] or "{}"),
                "created_at": row[7],
                "updated_at": row[8]
            }
    finally:
        conn.close()

def update_order_payload(db_id: int, new_raw_payload: dict) -> None:
    """Updates a broken order payload and pushes it back into the queue to be processed."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE queue
                SET raw_payload = %s,
                    status = 'PENDING',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(new_raw_payload), db_id))
        conn.commit()
    finally:
        conn.close()