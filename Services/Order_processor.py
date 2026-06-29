from Database.database import (
    get_next_pending_order,
    update_order_status,
    increment_retry,
)
from Services.csv_generator import clean_and_transform_data
from Services.warehouse import upload_via_sftp
from Services.alerts import send_critical_alert
import os

def process_engine_worker():
    """ORCASTARTES QUEUE MANAGEMENT | EXECUTION LOGS | AUTOMATED ERROR CATCHING"""
    
    order =  get_next_pending_order()

    if order is None:
        return
    
    raw_payload = order["raw_payload"]
    db_id = order["db_id"]
    order_id = order["order_id"]
    retry_count = order["retry_count"]

    try:
        update_order_status(db_id, 'PROCESSING')

        local_csv = clean_and_transform_data(raw_payload)

        upload_via_sftp(local_csv)

        if os.path.exists(local_csv):
            os.remove(local_csv)

        update_order_status(db_id, 'COMPLETED')

    except Exception as e:

        if retry_count < 3:
            increment_retry(db_id)

            update_order_status(db_id, 'RETRY_PENDING')
        
        else:
            update_order_status(db_id, 'HELD_FOR_REVIEW')

            send_critical_alert(db_id,str(e))



