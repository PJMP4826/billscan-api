from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from src.domain.value_objects.tax_detail import TaxDetail


@dataclass(frozen=True)
class TotalsAndTaxes:
    subtotal: Optional[Decimal] = None
    total_discount: Optional[Decimal] = Decimal("0.00")
    taxes: list[TaxDetail] = field(default_factory=list) # type: ignore
    total: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    change: Decimal | None = None

    def __post_init__(self) -> None:
        if self.subtotal is not None and self.subtotal < Decimal("0.00"):
            raise ValueError(
                f"subtotal must be >= 0, got {self.subtotal}."
            )
        if self.total_discount is not None and self.total_discount < Decimal("0.00"):
            raise ValueError(
                f"total_discount must be >= 0, got {self.total_discount}."
            )
        if self.total < Decimal("0.00"):
            raise ValueError(
                f"total must be >= 0, got {self.total}."
            )
        if self.amount_paid < Decimal("0.00"):
            raise ValueError(
                f"amount_paid must be >= 0, got {self.amount_paid}."
            )
        # Verify total is consistent: total >= sum(taxes) - discount
        taxes_sum = sum(t.amount for t in self.taxes)
        discount = self.total_discount or Decimal("0.00")
        subtotal = self.subtotal
        if subtotal is not None:
            expected_total = subtotal - discount + taxes_sum
            # Allow a tiny rounding tolerance of 1 cent
            if abs(self.total - expected_total) > Decimal("0.01"):
                raise ValueError(
                    f"Total ({self.total}) is inconsistent with "
                    f"subtotal ({subtotal}) - discount ({discount}) + taxes ({taxes_sum}) "
                    f"= {expected_total} (tolerance: ±0.01)."
                )

        if self.change is not None:
            if self.change < Decimal("0.00"):
                raise ValueError(f"change must be >= 0, got {self.change}.")
        
            expected_change = self.amount_paid - self.total
            # si expected_change < 0 -> pago insuficiente
            if expected_change < Decimal("0.00"):
                raise ValueError(
                    f"Insufficient payment: amount_paid ({self.amount_paid}) < total ({self.total})."
                )
        
            if abs(self.change - expected_change) > Decimal("0.01"):
                raise ValueError(
                    f"Change ({self.change}) is inconsistent with "
                    f"Amount paid ({self.amount_paid}) - total ({self.total}) = {expected_change}."
                )

