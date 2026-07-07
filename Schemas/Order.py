# Schemas/Order.py
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class LineItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    sku: str
    qty: int = Field(alias="quantity")


class CustomerInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str
    address: str


class OrderPayload(BaseModel):
    """
    Canonical webhook payload contract (v1.0).
    Accepts snake_case and camelCase field names.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    schema_version: Literal["1.0"] = Field(default="1.0", alias="schemaVersion")
    order_id: int = Field(alias="orderId")
    timestamp: str
    customer: CustomerInfo
    line_items: List[LineItem] = Field(default_factory=list, alias="lineItems")
