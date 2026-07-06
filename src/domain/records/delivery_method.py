from dataclasses import dataclass


@dataclass
class DeliveryMethod:
    method: str
    files_available: bool
    email_recipient: str | None = None
    message: str | None = None
