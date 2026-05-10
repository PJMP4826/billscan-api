from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal


class TaxDetail(BaseModel):
    name: str = Field(
        ...,
        description=(
            "Nombre del impuesto. En México: 'IVA', 'I.V.A.', 'IVA Trasladado', "
            "'Impuesto al Valor Agregado', 'IEPS' (Impuesto Especial), "
            "'IVA 16%', 'IVA 8%' (frontera norte), 'IVA 0%' (exento). "
            "Suele aparecer en el desglose del ticket o al pie en la sección de impuestos."
        ),
    )
    rate: Optional[Decimal] = Field(
        None,
        description=(
            "Porcentaje del impuesto. En México: 16.0 (tasa general), "
            "8.0 (frontera norte), 0.0 (exento). "
            "El IEPS varía según el producto (gasolina, alcohol, etc.). "
            "Suele aparecer entre paréntesis: 'IVA (16%) $12.34'."
        ),
    )
    amount: Decimal = Field(
        ...,
        description=(
            "Monto del impuesto en pesos mexicanos. "
            "En México suele aparecer como '$12.34' en la sección de "
            "'DESGLOSE DE IMPUESTOS' o 'IMPUESTOS TRASLADADOS': "
            "al pie del ticket. En algunos tickets el IVA se desglosa "
            "al final, no por producto. Si el ticket no desglosa impuestos, "
            "usa amount=0 y rate=0."
        ),
    )

    @field_validator('rate', 'amount', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
