from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class TransactionMetadata:
    date: Optional[str] = None
    time: Optional[str] = None
    receipt_id: Optional[str] = None
    pos_id: Optional[str] = None
    cashier: Optional[str] = None

    def __post_init__(self) -> None:
        if self.date is not None:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.date):
                raise ValueError(
                    f"Invalid date format '{self.date}'. Expected YYYY-MM-DD."
                )
        if self.time is not None:
            if not re.match(r"^\d{2}:\d{2}$", self.time):
                raise ValueError(
                    f"Invalid time format '{self.time}'. Expected HH:MM."
                )
        if self.receipt_id is not None and not self.receipt_id.strip():
            raise ValueError("receipt_id must not be an empty string.")
