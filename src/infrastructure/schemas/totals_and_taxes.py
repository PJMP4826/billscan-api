from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal
from src.infrastructure.schemas.tax_detail import TaxDetail


class TotalsAndTaxes(BaseModel):
    subtotal: Optional[Decimal] = Field(
        None,
        description=(
            "Suma antes de impuestos y descuentos, en pesos mexicanos. "
            "En México aparece como 'Subtotal:', 'Importe:', 'Suma parcial:', "
            "o 'Sin IVA'. En gasolineras suele llamarse 'Importe sin IVA' "
            "o 'Subtotal'. En Walmart/Soriana suele estar sobre la línea del IVA."
        ),
    )
    total_discount: Optional[Decimal] = Field(
        Decimal("0.00"),
        description=(
            "Suma total de descuentos en pesos mexicanos. "
            "En México: 'Descuento total:', 'Promociones:', 'Ahorro:', "
            "'Total Dto.', 'OFERTAS'. No incluyas aquí los descuentos individuales "
            "por producto (ve en LineItem). "
            "Si el ticket dice 'USTED AHORRÓ $X', ese es el total_discount."
        ),
    )
    taxes: list[TaxDetail] = Field( # type: ignore
        default_factory=list,
        description=(
            "Desglose de los impuestos trasladados. "
            "En México típicamente contiene 1-3 impuestos: IVA (16% u 8%), "
            "IEPS (variable). En tickets de gasolineras Pemex/G500 "
            "aparece desglosado: 'IVA 16% $X.XX', 'IEPS $Y.YY'. "
            "Si el ticket no desglosa impuestos (ej. tienda pequeña), "
            "pon la lista vacía."
        ),
    )
    total: Decimal = Field(
        ...,
        description=(
            "Monto final total pagado en pesos mexicanos. "
            "En México: 'Total:', 'TOTAL A PAGAR:', 'Importe Total:', "
            "'Total a Pagar', 'GRAN TOTAL'. Es generalmente el número más grande "
            "y destacado del ticket (en negritas, fuente más grande, "
            "o con signo $). "
            "No confundir con subtotal ni con 'Total Impuestos'."
        ),
    )

    @field_validator('subtotal', 'total_discount', 'total', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
