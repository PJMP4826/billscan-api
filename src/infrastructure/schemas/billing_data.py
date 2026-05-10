from pydantic import BaseModel, Field
from typing import Optional


class BillingData(BaseModel):
    is_billable: bool = Field(..., description="Verdadero si el ticket contiene instrucciones explícitas para solicitar factura fiscal.")
    billing_url: Optional[str] = Field(None, description="Sitio web o portal indicado para facturar.")
    billing_code: Optional[str] = Field(None, description="Código alfanumérico largo, clave de rastreo o referencia para obtener la factura.")
    expiration_date: Optional[str] = Field(None, description="Fecha límite para facturar.")
