from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class RecentActivityItem:
    comercio: str
    file_url: str
    fecha_alta: str
    total: Decimal
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "comercio": self.comercio,
            "file_url": self.file_url,
            "fecha_alta": self.fecha_alta,
            "total": str(self.total),
        }
