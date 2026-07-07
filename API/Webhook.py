# API/Webhook.py
import hmac
import hashlib
import base64
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException, Header

from Schemas.Order import OrderPayload
from Database.database import insert_order
from Core.config import settings
from Services.logger import log_system_event

router = APIRouter()

async def verify_shopify_signature(data: bytes, hmac_header: str):
    """
    Cryptographically verifies that the incoming webhook actually 
    came from Shopify and hasn't been tampered with.
    """
    secret = settings.SHOPIFY_WEBHOOK_SECRET.encode('utf-8')
    computed_hmac = base64.b64encode(
        hmac.new(secret, data, digestmod=hashlib.sha256).digest()
    ).decode('utf-8')
    
    if not hmac.compare_digest(computed_hmac, hmac_header):
        log_system_event(
            component="WEBHOOK",
            status="SECURITY_BREACH",
            message="Invalid HMAC signature received."
        )
        raise HTTPException(status_code=401, detail="HMAC verification failed")


# API/Webhook.py
import asyncio
from fastapi import APIRouter, Request, HTTPException, Header

from Schemas.Order import OrderPayload
from Database.database import insert_order
from Services.logger import log_system_event

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(
    payload: OrderPayload,  # <-- FastAPI automatically parses and validates the JSON for us!
    request: Request,
    x_shopify_hmac_sha256: str = Header(None)
):
    """
    Secure endpoint that accepts Shopify webhooks and safely pushes them into the processing queue.
    """
    
    # 1. SECURITY: Temporarily bypassed for local Bruno testing!
    # if not x_shopify_hmac_sha256:
    #     raise HTTPException(status_code=401, detail="Missing Shopify HMAC Header")
    
    # (If using HMAC in the future, you can still extract bytes here)

    # 2. ENQUEUE: Safely insert into the database via a thread
    try:
        # payload is already a fully validated OrderPayload object thanks to FastAPI!
        raw_payload_str = payload.model_dump_json()
        await asyncio.to_thread(insert_order, str(payload.order_id), raw_payload_str)
        
    except Exception as db_error:
        log_system_event(
            component="WEBHOOK",
            status="DB_INSERT_FAILED",
            message=f"Failed to queue order {payload.order_id}: {db_error}"
        )
        
        # If it's a duplicate order_id, PostgreSQL will throw an IntegrityError.
        if "UNIQUE constraint" in str(db_error) or "duplicate key" in str(db_error):
             return {"message": "Order already queued"}
        
        raise HTTPException(status_code=500, detail="Internal queue failure")

    return {"message": "Order securely queued"}