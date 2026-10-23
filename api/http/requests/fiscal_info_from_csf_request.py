from pydantic import BaseModel, EmailStr, Field

from src.domain.enums.invoice_use import InvoiceUse


class CreateFiscalInfoFromCsfRequest(BaseModel):
    """Datos que la constancia **no** trae y el usuario debe enviar.

    El archivo (``file``) no se declara aquí porque ``UploadFile`` no es
    validable por pydantic: el endpoint lo recibe como ``File(...)`` y lo pasa
    al controller por separado.
    """

    email: EmailStr = Field(..., description="Email de contacto fiscal")
    use_cfdi_code_default: InvoiceUse = Field(
        ..., description="Uso de CFDI por defecto (usado para la facturación)"
    )
