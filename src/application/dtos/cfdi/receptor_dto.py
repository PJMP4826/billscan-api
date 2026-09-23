from dataclasses import dataclass
from typing import Any


@dataclass
class ReceptorDto:
    """Nodo Receptor del CFDI."""

    rfc: str
    nombre: str
    domicilio_fiscal_receptor: str
    regimen_fiscal_receptor: str
    uso_cfdi: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReceptorDto":
        return cls(
            rfc=data["Rfc"],
            nombre=data["Nombre"],
            domicilio_fiscal_receptor=data["DomicilioFiscalReceptor"],
            regimen_fiscal_receptor=data["RegimenFiscalReceptor"],
            uso_cfdi=data["UsoCFDI"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rfc": self.rfc,
            "nombre": self.nombre,
            "domicilio_fiscal_receptor": self.domicilio_fiscal_receptor,
            "regimen_fiscal_receptor": self.regimen_fiscal_receptor,
            "uso_cfdi": self.uso_cfdi,
        }
