# API/Webhook.py
import asyncio
import base64
import hashlib
import hmac
import json
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import ValidationError

from Core.config import settings
from Database.database import insert_order
from Schemas.Order import OrderPayload
from Services.logger import log_system_event

router = APIRouter()
DEBUG_LOG_PATH = Path("debug-6ba292.log")


def _write_debug_log(payload: dict) -> None:
    payload.setdefault("sessionId", "6ba292")
    payload.setdefault("timestamp", int(time.time() * 1000))
    payload.setdefault("id", f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}")
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")


def verify_shopify_signature(raw_body: bytes, hmac_header: str) -> None:
    secret = settings.SHOPIFY_WEBHOOK_SECRET.encode("utf-8")
    computed_hmac = base64.b64encode(
        hmac.new(secret, raw_body, digestmod=hashlib.sha256).digest()
    ).decode("utf-8")

    if not hmac.compare_digest(computed_hmac, hmac_header):
        log_system_event(
            component="WEBHOOK",
            status="SECURITY_BREACH",
            message="Invalid HMAC signature received.",
        )
        raise HTTPException(status_code=401, detail="HMAC verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_shopify_hmac_sha256: str | None = Header(None),
):
    """
    Secure endpoint that accepts order webhooks and queues them for processing.
    Raw body is verified before JSON parsing so HMAC checks are trustworthy.
    """
    raw_body = await request.body()

    if settings.WEBHOOK_HMAC_REQUIRED:
        if not x_shopify_hmac_sha256:
            raise HTTPException(status_code=401, detail="Missing Shopify HMAC header")
        verify_shopify_signature(raw_body, x_shopify_hmac_sha256)
    elif x_shopify_hmac_sha256 and settings.SHOPIFY_WEBHOOK_SECRET:
        verify_shopify_signature(raw_body, x_shopify_hmac_sha256)

    try:
        payload = OrderPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        # #region agent log
        _write_debug_log({
            "runId": "pre-fix",
            "hypothesisId": "H1-H4",
            "location": "API/Webhook.py:receive_webhook:validation",
            "message": "OrderPayload validation failed",
            "data": {"errors": exc.errors(), "bodyPreview": raw_body[:1200].decode("utf-8", errors="ignore")},
        })
        # #endregion
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

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
            "schema_version": payload.schema_version,
        },
    })
    # #endregion

    try:
        raw_payload_str = payload.model_dump_json()
        await asyncio.to_thread(insert_order, str(payload.order_id), raw_payload_str)
    except Exception as db_error:
        log_system_event(
            component="WEBHOOK",
            status="DB_INSERT_FAILED",
            message=f"Failed to queue order {payload.order_id}: {db_error}",
        )

        if "UNIQUE constraint" in str(db_error) or "duplicate key" in str(db_error):
            return {"message": "Order already queued"}

        raise HTTPException(status_code=500, detail="Internal queue failure") from db_error

    return {"message": "Order securely queued", "order_id": payload.order_id}
