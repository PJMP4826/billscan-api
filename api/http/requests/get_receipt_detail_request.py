from pydantic import BaseModel


class GetReceiptDetailRequest(BaseModel):
    receipt_uuid: str
