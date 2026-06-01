import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PaymentInfo:
    method: str
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.method or not self.method.strip():
            raise ValueError("Payment method must not be empty.")
        if self.card_last_four is not None:
            if not re.match(r"^\d{4}$", self.card_last_four):
                raise ValueError(
                    f"card_last_four must be exactly 4 digits, got '{self.card_last_four}'."
                )
