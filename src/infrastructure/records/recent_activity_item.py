from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class RecentActivityItem:
    comercio: str | None
    file_url: str | None
    fecha_alta: str
    total: Decimal
    status: str | None
