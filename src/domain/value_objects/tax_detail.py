from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TaxDetail:
    name: str
    rate: Optional[Decimal] = None
    amount: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Tax name must not be empty.")
        if self.rate is not None:
            if self.rate < Decimal("0"):
                raise ValueError(
                    f"Tax rate must be >= 0, got {self.rate}."
                )
            if self.rate > Decimal("100"):
                raise ValueError(
                    f"Tax rate must be <= 100, got {self.rate}."
                )
        if self.amount < Decimal("0.00"):
            raise ValueError(
                f"Tax amount must be >= 0, got {self.amount}."
            )
