from pydantic import BaseModel, Field
from typing import Optional


class PaymentInfo(BaseModel):
    method: str = Field(
        ...,
        description=(
            "Método de pago. En México: 'Tarjeta de Débito', "
            "'Tarjeta de Crédito', 'Efectivo', 'Transferencia', "
            "'SPEI', 'Vales de Despensa', 'Tarjeta de Regalo', "
            "'Pago Mixto' (cuando usan efectivo + tarjeta), "
            "'Criptomonedas', 'Tarjeta', 'CASH', 'T.Débito'. "
            "Normaliza a español. Si usaron múltiples métodos, "
            "pon el principal (el de mayor importe). "
            "PEMEX acepta 'Efectivo' y 'Tarjeta' (Visa/MC). "
            "OXXO acepta 'Efectivo' y 'Tarjeta' (contactless)."
        ),
    )
    
    card_last_four: Optional[str] = Field(
        None,
        description=(
            "Últimos 4 dígitos de la tarjeta. En México aparece como: "
            "'Tarjeta: **** 1234', 'Cuenta: ********1234', "
            "'Últimos dígitos: 1234', 'TDBT **** 5678'. "
            "En tickets de OXXO y tiendas de conveniencia suele aparecer "
            "en la sección de pago si fue con tarjeta."
        ),
    )
    authorization_code: Optional[str] = Field(
        None,
        description=(
            "Número de autorización bancaria. En México: 'Aut.: 123456', "
            "'Aprobación: 987654', 'Código de autorización: AB1234Z', "
            "'Autorización: 00 12 34', 'REF: 567890'. "
            "Suele ser un código alfanumérico de 6-12 caracteres. "
            "Si no hay pago con tarjeta, déjalo vacío."
        ),
    )
