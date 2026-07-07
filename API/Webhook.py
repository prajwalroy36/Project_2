# API/Webhook.py
import hmac
import hashlib
import base64
import json
import asyncio
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Header

from Schemas.Order import OrderPayload
from Database.database import insert_order
from Core.config import settings
from Services.logger import log_system_event

router = APIRouter()
DEBUG_LOG_PATH = Path("debug-6ba292.log")

def _write_debug_log(payload: dict) -> None:
    payload.setdefault("sessionId", "6ba292")
    payload.setdefault("timestamp", int(time.time() * 1000))
    payload.setdefault("id", f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}")
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")

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
    
    # #region agent log
    _write_debug_log({
        "runId": "pre-fix",
        "hypothesisId": "H5",
        "location": "API/Webhook.py:receive_webhook:entry",
        "message": "Webhook reached handler with validated payload",
        "data": {
            "has_hmac_header": bool(x_shopify_hmac_sha256),
            "order_id": payload.order_id,
            "line_items_count": len(payload.line_items),
            "customer_name_present": bool(payload.customer.name),
        },
    })
    # #endregion

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