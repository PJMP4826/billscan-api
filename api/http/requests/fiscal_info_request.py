from csf_scraper import Rfc

from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.domain.enums.invoice_use import InvoiceUse

from pydantic import BaseModel, EmailStr, Field


class CreateFiscalInfoRequest(BaseModel):
    rfc: Rfc = Field(..., min_length=12, max_length=13, description="RFC del usuario")
    razon_social: str = Field(..., min_length=1)
    email: EmailStr = Field(..., description="Email de contacto fiscal")
    cp: str = Field(..., min_length=5, max_length=5, description="Código Postal")
    address: str | None = Field(default=None, description="Dirección opcional")
    regimens: list[BillingCustomerRegimeDto] = Field(
        ..., description="Lista de regimes con codigo y fecha de alta en el sat"
    )
    use_cfdi_code_default: InvoiceUse = Field(
        ..., description="Código str de Uso de Cfdi (usado para la facturacion)"
    )
