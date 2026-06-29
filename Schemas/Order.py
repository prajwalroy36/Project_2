from pydantic import BaseModel
from typing import List

# DATA VALIDATION MODULES

class LineItem(BaseModel):
    sku : str
    qty: int


class  CustomerInfo(BaseModel):
    name : str
    address : str



class OrderPayload(BaseModel):
    order_id : int
    timestamp : str
    customer : CustomerInfo
    line_items : List[LineItem]