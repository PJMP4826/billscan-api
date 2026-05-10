from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal


class PaymentInfo(BaseModel):
    method: str = Field(..., description="Método de pago principal (ej. Tarjeta de Débito, Efectivo).")
    amount_paid: Decimal = Field(..., description="Monto pagado con este método.")
    card_last_four: Optional[str] = Field(None, description="Últimos 4 dígitos de la tarjeta si aplica.")
    authorization_code: Optional[str] = Field(None, description="Número de autorización bancaria.")

    @field_validator('amount_paid', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
