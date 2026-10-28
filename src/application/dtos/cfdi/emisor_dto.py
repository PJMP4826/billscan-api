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
            rfc=data["rfc"],
            nombre=data["nombre"],
            regimen_fiscal=data["regimen_fiscal"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rfc": self.rfc,
            "nombre": self.nombre,
            "regimen_fiscal": self.regimen_fiscal,
        }
