from pydantic import BaseModel


class GetCfdiDetailRequest(BaseModel):
    receipt_uuid: str
