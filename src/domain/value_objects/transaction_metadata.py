from dataclasses import dataclass
from typing import Optional
from datetime import date, time

@dataclass(frozen=True)
class TransactionMetadata:
    transaction_date: Optional[date] = None
    transaction_time: Optional[time] = None
    receipt_id: Optional[str] = None
    pos_id: Optional[str] = None
    cashier: Optional[str] = None

    def __post_init__(self) -> None:
        if self.receipt_id is not None and not self.receipt_id.strip():
            raise ValueError("receipt_id must not be an empty string.")
