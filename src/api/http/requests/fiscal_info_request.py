from pydantic import BaseModel, EmailStr, Field


class CreateFiscalInfoRequest(BaseModel):
    rfc: str = Field(..., min_length=12, max_length=13, description="RFC del usuario")
    razon_social: str = Field(..., min_length=1)
    email: EmailStr = Field(..., description="Email de contacto fiscal")
    cp: str = Field(..., min_length=5, max_length=5, description="Código Postal")
    address: str | None = Field(default=None, description="Dirección opcional")
    regimen_code: str = Field(..., description="Código del régimen fiscal (ej. '601')")