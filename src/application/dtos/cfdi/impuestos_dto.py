from dataclasses import dataclass
from typing import Any


@dataclass
class TrasladoDto:
    """Un traslado de impuesto (ej. IVA) dentro de un nodo Impuestos."""

    base: float
    impuesto: str
    tipo_factor: str
    tasa_o_cuota: float
    importe: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrasladoDto":
        return cls(
            base=data["Base"],
            impuesto=data["Impuesto"],
            tipo_factor=data["TipoFactor"],
            tasa_o_cuota=data["TasaOCuota"],
            importe=data["Importe"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "Base": self.base,
            "Impuesto": self.impuesto,
            "TipoFactor": self.tipo_factor,
            "TasaOCuota": self.tasa_o_cuota,
            "Importe": self.importe,
        }


@dataclass
class ImpuestosDto:
    """Nodo Impuestos del CFDI y de cada concepto con objeto de impuesto."""

    traslados: dict[str, TrasladoDto]
    total_impuestos_trasladados: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImpuestosDto":
        traslados_raw: dict[str, Any] = data.get("Traslados") or {}
        return cls(
            traslados={
                key: TrasladoDto.from_dict(value)
                for key, value in traslados_raw.items()
            },
            total_impuestos_trasladados=data.get("TotalImpuestosTrasladados"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "Traslados": {
                key: traslado.to_dict()
                for key, traslado in self.traslados.items()
            },
        }
        if self.total_impuestos_trasladados is not None:
            result["TotalImpuestosTrasladados"] = self.total_impuestos_trasladados
        return result
