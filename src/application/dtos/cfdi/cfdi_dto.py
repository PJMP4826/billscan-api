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
        """Hidrata el DTO desde un payload canónico en ``snake_case``.

        El payload lo produce ``CfdiPayloadMapper`` (adaptador de
        infraestructura) a partir del XML del SAT, y es el mismo formato que
        ``to_dict()`` persiste en la columna ``cfdi_summary``.
        """
        impuestos_raw = data.get("impuestos")
        return cls(
            emisor=EmisorDto.from_dict(data["emisor"]),
            receptor=ReceptorDto.from_dict(data["receptor"]),
            conceptos=[ConceptosDto.from_dict(item) for item in data["conceptos"]],
            complemento=ComplementoDto.from_dict(data["complemento"]),
            version=data["version"],
            fecha=data["fecha"],
            forma_pago=data["forma_pago"],
            sub_total=data["sub_total"],
            moneda=data["moneda"],
            total=data["total"],
            tipo_de_comprobante=data["tipo_de_comprobante"],
            exportacion=data["exportacion"],
            metodo_pago=data["metodo_pago"],
            lugar_expedicion=data["lugar_expedicion"],
            impuestos=(
                ImpuestosDto.from_dict(impuestos_raw)
                if impuestos_raw is not None
                else None
            ),
            serie=data.get("serie"),
            folio=data.get("folio"),
            condiciones_de_pago=data.get("condiciones_de_pago"),
            tipo_cambio=data.get("tipo_cambio"),
            descuento=data.get("descuento"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "emisor": self.emisor.to_dict(),
            "receptor": self.receptor.to_dict(),
            "conceptos": [concepto.to_dict() for concepto in self.conceptos],
            "complemento": self.complemento.to_dict(),
            "version": self.version,
            "fecha": self.fecha,
            "forma_pago": self.forma_pago,
            "sub_total": self.sub_total,
            "moneda": self.moneda,
            "total": self.total,
            "tipo_de_comprobante": self.tipo_de_comprobante,
            "exportacion": self.exportacion,
            "metodo_pago": self.metodo_pago,
            "lugar_expedicion": self.lugar_expedicion,
            "impuestos": (
                self.impuestos.to_dict() if self.impuestos is not None else None
            ),
            "serie": self.serie,
            "folio": self.folio,
            "condiciones_de_pago": self.condiciones_de_pago,
            "tipo_cambio": self.tipo_cambio,
            "descuento": self.descuento,
        }
        return result
