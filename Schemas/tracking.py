# Schemas/tracking.py
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrackingRecord(BaseModel):
    """Strict contract for warehouse tracking CSV rows."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore", str_strip_whitespace=True)

    order_id: str = Field(alias="orderId", min_length=1)
    tracking_number: str = Field(alias="trackingNumber", min_length=1)
    carrier: str = Field(min_length=1)

    @field_validator("order_id", "tracking_number", "carrier")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()
