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
        impuestos_raw = data.get("Impuestos")
        return cls(
            clave_prod_serv=data["ClaveProdServ"],
            cantidad=data["Cantidad"],
            clave_unidad=data["ClaveUnidad"],
            descripcion=data["Descripcion"],
            valor_unitario=data["ValorUnitario"],
            importe=data["Importe"],
            objeto_imp=data["ObjetoImp"],
            impuestos=(
                ImpuestosDto.from_dict(impuestos_raw)
                if impuestos_raw is not None
                else None
            ),
            no_identificacion=data.get("NoIdentificacion"),
            unidad=data.get("Unidad"),
            descuento=data.get("Descuento"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ClaveProdServ": self.clave_prod_serv,
            "Cantidad": self.cantidad,
            "ClaveUnidad": self.clave_unidad,
            "Descripcion": self.descripcion,
            "ValorUnitario": self.valor_unitario,
            "Importe": self.importe,
            "ObjetoImp": self.objeto_imp,
        }
        if self.impuestos is not None:
            result["Impuestos"] = self.impuestos.to_dict()
        if self.no_identificacion is not None:
            result["NoIdentificacion"] = self.no_identificacion
        if self.unidad is not None:
            result["Unidad"] = self.unidad
        if self.descuento is not None:
            result["Descuento"] = self.descuento
        return result
