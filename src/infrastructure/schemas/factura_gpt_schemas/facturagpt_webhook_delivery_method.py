from pydantic import BaseModel


class FacturaGPTWebhookDeliveryMethod(BaseModel):
    method: str 
    files_available: bool
    email_recipient: str | None = None
    message: str | None = None
