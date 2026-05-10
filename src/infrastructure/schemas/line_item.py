from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any, Optional
from src.infrastructure.shared.clean_decimal import clean_decimal


class LineItem(BaseModel):
    quantity: float = Field(..., description="Cantidad comprada del artículo. (Puede ser float si es a granel, ej. 1.5 kg)")
    description: str = Field(..., description="Nombre o descripción del producto.")
    sku: Optional[str] = Field(None, description="Código de barras o SKU del producto.")
    
    unit_price: Optional[Decimal] = Field(None, description="Precio unitario.")
    total_price: Decimal = Field(..., description="Precio total por esta línea.")
    discount: Optional[Decimal] = Field(Decimal("0.00"), description="Monto descontado.")

    @field_validator('unit_price', 'total_price', 'discount', mode='before')
    @classmethod
    def parse_money_fields(cls, v: Any) -> Any:
        return clean_decimal(v)
