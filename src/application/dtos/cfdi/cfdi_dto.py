from dataclasses import dataclass
from typing import Any

from src.application.dtos.cfdi.complemento_dto import ComplementoDto
from src.application.dtos.cfdi.conceptos_dto import ConceptosDto
from src.application.dtos.cfdi.emisor_dto import EmisorDto
from src.application.dtos.cfdi.impuestos_dto import ImpuestosDto
from src.application.dtos.cfdi.receptor_dto import ReceptorDto


@dataclass
class CfdiDto:
    """Contenido de un CFDI de tipo Ingreso (I) serializado por CfdiParser."""

    emisor: EmisorDto
    receptor: ReceptorDto
    conceptos: list[ConceptosDto]
    complemento: ComplementoDto
    version: str
    fecha: str
    forma_pago: str
    sub_total: float
    moneda: str
    total: float
    tipo_de_comprobante: str
    exportacion: str
    metodo_pago: str
    lugar_expedicion: str
    impuestos: ImpuestosDto | None = None
    serie: str | None = None
    folio: str | None = None
    condiciones_de_pago: str | None = None
    tipo_cambio: float | None = None
    descuento: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CfdiDto":
        impuestos_raw = data.get("Impuestos")
        return cls(
            emisor=EmisorDto.from_dict(data["Emisor"]),
            receptor=ReceptorDto.from_dict(data["Receptor"]),
            conceptos=[
                ConceptosDto.from_dict(item) for item in data["Conceptos"]
            ],
            complemento=ComplementoDto.from_dict(data["Complemento"]),
            version=data["Version"],
            fecha=data["Fecha"],
            forma_pago=data["FormaPago"],
            sub_total=data["SubTotal"],
            moneda=data["Moneda"],
            total=data["Total"],
            tipo_de_comprobante=data["TipoDeComprobante"],
            exportacion=data["Exportacion"],
            metodo_pago=data["MetodoPago"],
            lugar_expedicion=data["LugarExpedicion"],
            impuestos=(
                ImpuestosDto.from_dict(impuestos_raw)
                if impuestos_raw is not None
                else None
            ),
            serie=data.get("Serie"),
            folio=data.get("Folio"),
            condiciones_de_pago=data.get("CondicionesDePago"),
            tipo_cambio=data.get("TipoCambio"),
            descuento=data.get("Descuento"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "Emisor": self.emisor.to_dict(),
            "Receptor": self.receptor.to_dict(),
            "Conceptos": [concepto.to_dict() for concepto in self.conceptos],
            "Complemento": self.complemento.to_dict(),
            "Version": self.version,
            "Fecha": self.fecha,
            "FormaPago": self.forma_pago,
            "SubTotal": self.sub_total,
            "Moneda": self.moneda,
            "Total": self.total,
            "TipoDeComprobante": self.tipo_de_comprobante,
            "Exportacion": self.exportacion,
            "MetodoPago": self.metodo_pago,
            "LugarExpedicion": self.lugar_expedicion,
        }
        if self.impuestos is not None:
            result["Impuestos"] = self.impuestos.to_dict()
        if self.serie is not None:
            result["Serie"] = self.serie
        if self.folio is not None:
            result["Folio"] = self.folio
        if self.condiciones_de_pago is not None:
            result["CondicionesDePago"] = self.condiciones_de_pago
        if self.tipo_cambio is not None:
            result["TipoCambio"] = self.tipo_cambio
        if self.descuento is not None:
            result["Descuento"] = self.descuento
        return result
