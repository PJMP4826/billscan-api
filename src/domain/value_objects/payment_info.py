import re
from dataclasses import dataclass
from typing import Optional

from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)


@dataclass(frozen=True)
class PaymentInfo:
    method_code: Optional[SatPaymentMethodCode] = None
    method_description: Optional[SatPaymentMethodDescription] = None
    card_last_four: Optional[str] = None
    authorization_code: Optional[str] = None

    def __post_init__(self) -> None:
        # Ensure required fields are present
        if self.method_code is None:
            raise ValueError("Payment method code must not be empty.")
        if self.method_description is None:
            raise ValueError("Payment method description must not be empty.")

        # Validate enum types properly using isinstance
        if not isinstance(self.method_code, SatPaymentMethodCode): # type: ignore
            raise ValueError(
                f"method_code must be a SatPaymentMethodCode enum member, got {self.method_code!r}."
            )
        if not isinstance(self.method_description, SatPaymentMethodDescription): # type: ignore
            raise ValueError(
                f"method_description must be a SatPaymentMethodDescription enum member, got {self.method_description!r}."
            )
        if self.card_last_four is not None:
            if not re.match(r"^\d{4}$", self.card_last_four):
                raise ValueError(
                    f"card_last_four must be exactly 4 digits, got '{self.card_last_four}'."
                )
