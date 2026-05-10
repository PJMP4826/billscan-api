from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal


class TaxDetail(BaseModel):
    name: str = Field(..., description="Nombre del impuesto (ej. IVA, T.V.A.).")
    rate: Optional[Decimal] = Field(None, description="Porcentaje del impuesto (ej. 16.0, 8.0).")
    amount: Decimal = Field(..., description="Monto cobrado por este impuesto.")

    @field_validator('rate', 'amount', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
