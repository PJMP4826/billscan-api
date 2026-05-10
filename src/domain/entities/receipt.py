from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any
from src.domain.value_objects.merchant_data import MerchantData
from src.domain.value_objects.transaction_metadata import TransactionMetadata
from src.domain.value_objects.line_item import LineItem
from src.domain.value_objects.totals_and_taxes import TotalsAndTaxes
from src.domain.value_objects.payment_info import PaymentInfo
from src.domain.value_objects.billing_data import BillingData


@dataclass
class Receipt:
    """Entidad raíz del dominio que representa un ticket/recibo.

    A diferencia de los value objects (inmutables), Receipt tiene identidad
    propia (receipt_id) y puede mutar su estado a lo largo del ciclo de vida.
    """

    receipt_id: str
    merchant: MerchantData
    transaction: TransactionMetadata
    items: list[LineItem]
    totals: TotalsAndTaxes
    payment: PaymentInfo
    billing: BillingData | None = None
    context_notes: str | None = None

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.receipt_id.strip():
            raise ValueError("receipt_id must not be empty.")
        if not self.items:
            raise ValueError("A receipt must have at least one item.")

    def add_item(self, item: LineItem) -> None:
        """Agrega un artículo al recibo."""
        self.items.append(item)

    def total_items(self) -> int:
        return len(self.items)

    def subtotal_from_items(self) -> Decimal:
        """Calcula el subtotal a partir del total_price de cada ítem."""
        return sum((i.total_price for i in self.items), Decimal("0.00"))

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entidad y sus value objects anidados a un dict plano."""
        return asdict(self)
