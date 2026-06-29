import psycopg
from Core.config import settings


DATABASE_URL = settings.DATABASE_URL

def get_connection():
    
    return psycopg.connect(DATABASE_URL)

    
def insert_order(order_id:str, raw_payload:str)-> None:

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
         

         cursor.execute("""
         INSERT INTO queue(order_id,raw_payload,status,retry_count)
         VALUES(%s,%s,%s,%s)""",
         (order_id,raw_payload,"PENDING",0))
        
        conn.commit()
    finally:
        conn.close()
    
def get_next_pending_order()-> dict | None:

    conn = get_connection()

    try:
       
        with conn.cursor() as cursor:
            cursor.execute("""
                           SELECT 
                           id,order_id,raw_payload,retry_count
                           FROM queue WHERE STATUS IN ('PENDING', 'RETRY_PENDING')
                           ORDER BY id ASC LIMIT 1""")
            
            row = cursor.fetchone()

            if row is None:
                return None
            
            return {
                "db_id": row[0],
                "order_id":row[1],
                "raw_payload":row[2],
                "retry_count":row[3]
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
                           SELECT db_id, order_id, status, retry_count FROM queue
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
        