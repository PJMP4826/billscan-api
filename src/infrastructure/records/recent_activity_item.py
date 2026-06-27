from decimal import Decimal
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RecentActivityItem:
    comercio: str | None
    file_url: str | None
    fecha_alta: str
    total: Decimal
    status: str | None

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
