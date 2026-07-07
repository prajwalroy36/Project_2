# Schemas/Order.py
from pydantic import BaseModel, Field
from typing import List

class LineItem(BaseModel):
    sku: str
    qty: int

class CustomerInfo(BaseModel):
    name: str
    address: str

class OrderPayload(BaseModel):
    order_id: int
    timestamp: str
    customer: CustomerInfo
    line_items: List[LineItem] = Field(default_factory=list)

    class Config:
        # Allows Pydantic to read both snake_case, camelCase, or objects flexibly
        populate_by_name = True
        extra = "ignore"