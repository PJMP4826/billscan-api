from dataclasses import dataclass
from typing import Any


@dataclass
class EmisorDto:
    """Nodo Emisor del CFDI."""

    rfc: str
    nombre: str
    regimen_fiscal: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmisorDto":
        return cls(
            rfc=data["Rfc"],
            nombre=data["Nombre"],
            regimen_fiscal=data["RegimenFiscal"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "Rfc": self.rfc,
            "Nombre": self.nombre,
            "RegimenFiscal": self.regimen_fiscal,
        }
