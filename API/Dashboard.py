# API/Dashboard.py
from fastapi import APIRouter, Depends, Body, HTTPException
from Database.database import (
    get_recent_orders, 
    retry_held_order, 
    get_order_details, 
    update_order_payload
)
from API.security import get_api_key

# 1. Initialize the Router
# The Depends(get_api_key) locks down EVERY route in this file.
router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_api_key)] 
)

# ---------------------------------------------------------
# Feature 1: Overview Dashboard
# ---------------------------------------------------------
@router.get("/orders")
def fetch_recent_orders(limit: int = 100):
    """
    Returns the most recent orders to populate the main frontend table.
    Defaults to 100 to keep the UI fast, but the frontend can request more.
    """
    orders = get_recent_orders(limit=limit)
    return {"status": "success", "data": orders}

# ---------------------------------------------------------
# Feature 2: Lifecycle Tracking & Error Viewing
# ---------------------------------------------------------
@router.get("/orders/{db_id}")
def fetch_order_details(db_id: int):
    """
    Returns the complete lifecycle history, error reasons, and raw JSON payloads
    for a specific order. Used when clicking an order in the dashboard.
    """
    order = get_order_details(db_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"status": "success", "data": order}

# ---------------------------------------------------------
# Feature 3: Quick Retry
# ---------------------------------------------------------
@router.post("/orders/{db_id}/retry")
def trigger_manual_retry(db_id: int):
    """
    Instantly pushes a stuck (FAILED or HELD_FOR_REVIEW) order back into the queue.
    The autonomous_sending_loop will automatically pick it up.
    """
    retry_held_order(db_id)
    return {"status": "success", "message": f"Order {db_id} queued for retry."}

# ---------------------------------------------------------
# Feature 4: Edit Payload & Retry
# ---------------------------------------------------------
@router.put("/orders/{db_id}/edit")
def edit_and_retry_order(db_id: int, updated_payload: dict = Body(...)):
    """
    Saves a manually corrected payload (e.g., fixing a missing apartment number)
    and pushes the order back into the processing queue.
    """
    # Note: Body(...) tells FastAPI to expect a raw JSON object in the request body
    update_order_payload(db_id, updated_payload)
    return {"status": "success", "message": f"Order {db_id} updated and queued for retry."}