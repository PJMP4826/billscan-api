from typing import Literal
from pydantic import BaseModel, Field


class GetReceiptDetailRequest(BaseModel):
    receipt_uuid: str
    detail_level: Literal["base", "full"] = Field(default="base")
