from pydantic import BaseModel, Field
from typing import Optional

from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)


class PaymentInfo(BaseModel):
    method_code: SatPaymentMethodCode = Field(
        description=(
            "Código del método de pago según catálogo del SAT (ej. '01', '04', '28'). "
            "Usa los códigos oficiales del SAT cuando estén disponibles."
        ),
    )
    method_description: SatPaymentMethodDescription = Field(
        description=(
            "Descripción textual del método de pago en español. "
            "Normaliza a español. Si usaron múltiples métodos, "
            "pon el principal (el de mayor importe). "
            "ej. PEMEX acepta 'Efectivo' y 'Tarjeta' (Visa/MC). "
            "OXXO acepta 'Efectivo' y 'Tarjeta' (contactless)."
            "Debe usar únicamente una de las descripciones definidas en `SatPaymentMethodDescription` "
            "(ej. 'Efectivo', 'Tarjeta de crédito', 'Tarjeta de débito', 'Por definir')."
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
