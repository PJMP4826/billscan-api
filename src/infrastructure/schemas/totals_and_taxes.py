from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, List, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal
from src.infrastructure.schemas.tax_detail import TaxDetail


class TotalsAndTaxes(BaseModel):
    subtotal: Optional[Decimal] = Field(None, description="Suma antes de impuestos y descuentos.")
    total_discount: Optional[Decimal] = Field(Decimal("0.00"), description="Suma de descuentos.")
    taxes: List[TaxDetail] = Field(default_factory=list, description="Desglose de los impuestos.")
    total: Decimal = Field(..., description="Monto final total pagado.")

    @field_validator('subtotal', 'total_discount', 'total', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
