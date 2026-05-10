from pydantic import BaseModel, Field
from typing import Optional


class MerchantData(BaseModel):
    name: str = Field(..., description="Nombre comercial o razón social de la tienda.")
    tax_id: Optional[str] = Field(None, description="Identificador fiscal del emisor. RFC (12 o 13 caracteres), CUIT, etc.")
    address: Optional[str] = Field(None, description="Dirección completa de la sucursal.")
    branch_id: Optional[str] = Field(None, description="Número o identificador de la sucursal o tienda.")
    phone: Optional[str] = Field(None, description="Teléfono de contacto.")
