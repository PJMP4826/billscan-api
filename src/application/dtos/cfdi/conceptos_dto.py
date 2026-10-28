from dataclasses import dataclass
from typing import Any

from src.application.dtos.cfdi.impuestos_dto import ImpuestosDto


@dataclass
class ConceptosDto:
    """Un concepto (renglón) de la lista Conceptos del CFDI."""

    clave_prod_serv: str
    cantidad: float
    clave_unidad: str
    descripcion: str
    valor_unitario: float
    importe: float
    objeto_imp: str
    impuestos: ImpuestosDto | None = None
    no_identificacion: str | None = None
    unidad: str | None = None
    descuento: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConceptosDto":
        impuestos_raw = data.get("impuestos")
        return cls(
            clave_prod_serv=data["clave_prod_serv"],
            cantidad=data["cantidad"],
            clave_unidad=data["clave_unidad"],
            descripcion=data["descripcion"],
            valor_unitario=data["valor_unitario"],
            importe=data["importe"],
            objeto_imp=data["objeto_imp"],
            impuestos=(
                ImpuestosDto.from_dict(impuestos_raw)
                if impuestos_raw is not None
                else None
            ),
            no_identificacion=data.get("no_identificacion"),
            unidad=data.get("unidad"),
            descuento=data.get("descuento"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "clave_prod_serv": self.clave_prod_serv,
            "cantidad": self.cantidad,
            "clave_unidad": self.clave_unidad,
            "descripcion": self.descripcion,
            "valor_unitario": self.valor_unitario,
            "importe": self.importe,
            "objeto_imp": self.objeto_imp,
            "impuestos": (
                self.impuestos.to_dict() if self.impuestos is not None else None
            ),
            "no_identificacion": self.no_identificacion,
            "unidad": self.unidad,
            "descuento": self.descuento,
        }
        return result
