from pydantic import BaseModel, Field
from typing import Optional


class BillingData(BaseModel):
    is_billable: bool = Field(..., description="Verdadero si el ticket contiene instrucciones explícitas para solicitar factura fiscal.")
    has_qr_code: bool = Field(False, description="Verdadero si la URL fue obtenida escaneando un código QR del ticket.")
    billing_url: Optional[str] = Field(None, description="Sitio web o portal indicado para facturar.")
    billing_code: Optional[str] = Field(None, description="Código alfanumérico largo, clave de rastreo o referencia para obtener la factura.")
    barcode: Optional[str] = Field(None, description="Código de barras numérico largo impreso en el ticket (ej. 20210729003500709921).")
    expiration_date: Optional[str] = Field(None, description="Fecha límite para facturar en formato YYYY-MM-DD o texto como '30 días'.")
