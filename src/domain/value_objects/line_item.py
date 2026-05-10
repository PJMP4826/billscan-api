from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class LineItem:
    quantity: float
    description: str
    sku: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_price: Decimal = Decimal("0.00")
    discount: Optional[Decimal] = Decimal("0.00")

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}.")
        if not self.description or not self.description.strip():
            raise ValueError("Line item description must not be empty.")
        if self.unit_price is not None and self.unit_price < Decimal("0.00"):
            raise ValueError(
                f"unit_price must be >= 0, got {self.unit_price}."
            )
        if self.total_price < Decimal("0.00"):
            raise ValueError(
                f"total_price must be >= 0, got {self.total_price}."
            )
        if self.discount is not None and self.discount < Decimal("0.00"):
            raise ValueError(
                f"discount must be >= 0, got {self.discount}."
            )
        if self.total_price < (self.discount or Decimal("0.00")):
            raise ValueError(
                f"total_price ({self.total_price}) is less than discount ({self.discount})."
            )
