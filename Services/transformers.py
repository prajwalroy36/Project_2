# Services/transformers.py
from datetime import datetime, timedelta

from Schemas.Order import OrderPayload


def transform_order(raw_payload: str | dict) -> dict:
    """
    Converts the incoming order payload into a warehouse-ready payload.
    """
    if isinstance(raw_payload, str):
        payload = OrderPayload.model_validate_json(raw_payload)
    else:
        payload = OrderPayload.model_validate(raw_payload)

    customer_name = payload.customer.name
    full_address = payload.customer.address.strip()

    address_line_1 = full_address[:30]
    address_line_2 = full_address[30:60]
    address_line_3 = full_address[60:90]

    if len(full_address) > 90:
        raise ValueError("Address exceeds warehouse limit of 90 characters.")

    clean_timestamp = payload.timestamp.replace("Z", "+00:00")
    order_time = datetime.fromisoformat(clean_timestamp)

    if order_time.hour >= 10:
        delivery_date = order_time + timedelta(days=1)
    else:
        delivery_date = order_time

    if delivery_date.weekday() == 5:
        delivery_date += timedelta(days=2)
    elif delivery_date.weekday() == 6:
        delivery_date += timedelta(days=1)

    delivery_date_str = delivery_date.strftime("%m/%d/%Y")

    return {
        "order_id": payload.order_id,
        "customer_name": customer_name,
        "address_line_1": address_line_1,
        "address_line_2": address_line_2,
        "address_line_3": address_line_3,
        "delivery_date": delivery_date_str,
        "unit": "Each",
        "line_items": [
            {"sku": item.sku, "qty": item.qty}
            for item in payload.line_items
        ],
    }
