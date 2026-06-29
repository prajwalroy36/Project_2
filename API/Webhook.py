from fastapi import APIRouter,BackgroundTasks
from Schemas.Order import OrderPayload
from Database.database import insert_order
from Services.Order_processor import process_engine_worker







router = APIRouter()

@router.post("/webhook")
async def recieve_webhook(payload : OrderPayload, background_tasks: BackgroundTasks):

    

    order_id = payload.order_id

    raw_payload = payload.model_dump_json()

    insert_order(order_id,raw_payload)

    background_tasks.add_task(process_engine_worker)

    return {"message": "order accpeted"}








        
   


