# Services/transformers.py
from datetime import datetime, timedelta
from Schemas.Order import OrderPayload

def transform_order(raw_payload: str) -> dict:
    """
    Converts the incoming Shopify payload into a warehouse-ready payload.
    """
    # -----------------------------
    # Validate payload
    # -----------------------------
    # If raw_payload is already a dict, convert it or use model_validate
    if isinstance(raw_payload, str):
        payload = OrderPayload.model_validate_json(raw_payload)
    else:
        payload = OrderPayload.model_validate(raw_payload)

    # -----------------------------
    # Customer Information extraction
    # -----------------------------
    customer_name = payload.customer.name
    full_address = payload.customer.address.strip()
    
    # ... (keep the rest of your delivery date logic and line item mapping below)

    # -----------------------------
    # Address Split
    # -----------------------------
    address_line_1 = full_address[:30]
    address_line_2 = full_address[30:60]
    address_line_3 = full_address[60:90]

    # Warehouse limit
    if len(full_address) > 90:
        raise ValueError(
            "Address exceeds warehouse limit of 90 characters."
        )

    # -----------------------------
    # Delivery Date Rule
    # -----------------------------
    order_time = datetime.strptime(
        payload.timestamp,
        "%Y-%m-%dT%H:%M:%SZ"
    )

    clean_timestamp = payload.timestamp.replace("Z", "+00:00")
    order_time = datetime.fromisoformat(clean_timestamp)


    if order_time.hour >= 10:
        delivery_date = order_time + timedelta(days=1)
    else:
        delivery_date = order_time

    # Skip Saturday
    if delivery_date.weekday() == 5:
        delivery_date += timedelta(days=2)

    # Skip Sunday
    elif delivery_date.weekday() == 6:
        delivery_date += timedelta(days=1)

    delivery_date = delivery_date.strftime("%m/%d/%Y")

    # -----------------------------
    # Warehouse Payload
    # -----------------------------
    warehouse_payload = {

        "order_id": payload.order_id,

        "customer_name": customer_name,

        "address_line_1": address_line_1,

        "address_line_2": address_line_2,

        "address_line_3": address_line_3,

        "delivery_date": delivery_date,

        "unit": "Each",

        "line_items": [
            {
                "sku": item.sku,
                "qty": item.qty
            }
            for item in payload.line_items
        ]
    }

    return warehouse_payload


