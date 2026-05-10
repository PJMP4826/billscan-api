from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal


class LineItem(BaseModel):
    quantity: float = Field(
        ...,
        description=(
            "Cantidad del artículo. Float si es a granel (ej. 1.5 kg) o entero si es por pieza. "
            "En tickets mexicanos la cantidad puede aparecer antes de la descripción "
            "('3 x $45.00') o al inicio de la línea ('2.000 kg'). "
            "Si el ticket muestra '3x' al principio, la cantidad es 3. "
            "Si muestra 'PZA', 'KG', 'L', 'ML', son unidades de medida, no son la cantidad."
        ),
    )
    description: str = Field(
        ...,
        description=(
            "Nombre o descripción del producto. "
            "En tickets mexicanos suele estar abreviado (máx. 20-30 caracteres). "
            "Ej: 'ACEITE NUTRIOLI 946ML', 'GALLETAS PRINCIPE CHOC', 'LECHE LALA ENTERA 2L', "
            "'COCA-COLA 600ML NR', 'PAN BIMBO BLANCO 680G', 'JABON ZOTE 200G'. "
            "Si el texto está cortado, complétalo con tu conocimiento. "
            "No incluyas SKU, precio ni cantidad en este campo."
        ),
    )
    sku: Optional[str] = Field(
        None,
        description=(
            "Código de barras o SKU. En México: 13 dígitos (EAN-13, empieza con 750), "
            "12 dígitos (UPC-A), o código interno de tienda de 5-8 dígitos. "
            "Suele aparecer en la línea del producto como '7501234567890'. "
            "En Walmart/Soriana suele aparecer junto al nombre del producto. "
            "Si ves un número largo (12-13 dígitos) en la misma línea del producto, es el SKU."
        ),
    )
    unit_price: Optional[Decimal] = Field(
        None,
        description=(
            "Precio unitario en pesos mexicanos. "
            "En tickets puede aparecer como '$45.00 PU', 'P.U. $45.00', o sin etiqueta. "
            "No confundir con el precio total de la línea. "
            "Si multiplicas cantidad × precio unitario, debe dar ≈ precio total."
        ),
    )
    total_price: Decimal = Field(
        ...,
        description=(
            "Precio total por esta línea en pesos mexicanos. "
            "Es el importe que aparece al final de la línea, generalmente alineado a la derecha. "
            "Si la cantidad > 1, total_price ≈ cantidad × unit_price. "
            "En tickets mexicanos suele aparecer como '45.00', '$90.00', o tras un espacio amplio."
        ),
    )
    discount: Optional[Decimal] = Field(
        Decimal("0.00"),
        description=(
            "Monto descontado en esta línea, en pesos mexicanos. "
            "En México aparece como 'Desc. $5.00', 'Dto. $10.00', 'Promo -$15.00', "
            "'OFERTA -$7.50', o precedido por un signo negativo. "
            "Si el descuento aparece a nivel total (no por línea), ponlo en TotalsAndTaxes."
        ),
    )

    @field_validator('unit_price', 'total_price', 'discount', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
