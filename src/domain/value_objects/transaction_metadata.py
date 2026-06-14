from dataclasses import dataclass
from typing import Optional
from datetime import date, time


@dataclass(frozen=True)
class TransactionMetadata:
    transaction_date: Optional[date] = None
    transaction_time: Optional[time] = None
    ticket_number: Optional[str] = None
    pos_id: Optional[str] = None
    cashier: Optional[str] = None
