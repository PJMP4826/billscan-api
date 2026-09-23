from dataclasses import dataclass
from typing import Any


@dataclass
class TimbreFiscalDigitalDto:
    """Nodo TimbreFiscalDigital (sello del SAT) dentro del Complemento."""

    version: str
    uuid: str
    fecha_timbrado: str
    rfc_prov_certif: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimbreFiscalDigitalDto":
        return cls(
            version=data["Version"],
            uuid=data["UUID"],
            fecha_timbrado=data["FechaTimbrado"],
            rfc_prov_certif=data["RfcProvCertif"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "uuid": self.uuid,
            "fecha_timbrado": self.fecha_timbrado,
            "rfc_prov_certif": self.rfc_prov_certif,
        }


@dataclass
class CfdiRegistroFiscalDto:
    """Nodo CFDIRegistroFiscal dentro del Complemento (opcional)."""

    version: str
    folio: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CfdiRegistroFiscalDto":
        return cls(
            version=data["Version"],
            folio=data["Folio"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "folio": self.folio,
        }


@dataclass
class ComplementoDto:
    """Nodo Complemento del CFDI."""

    timbre_fiscal_digital: TimbreFiscalDigitalDto
    cfdi_registro_fiscal: CfdiRegistroFiscalDto | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComplementoDto":
        registro_raw = data.get("CFDIRegistroFiscal")
        return cls(
            timbre_fiscal_digital=TimbreFiscalDigitalDto.from_dict(
                data["TimbreFiscalDigital"]
            ),
            cfdi_registro_fiscal=(
                CfdiRegistroFiscalDto.from_dict(registro_raw)
                if registro_raw is not None
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "timbre_fiscal_digital": self.timbre_fiscal_digital.to_dict(),
        }
        if self.cfdi_registro_fiscal is not None:
            result["cfdi_registro_fiscal"] = self.cfdi_registro_fiscal.to_dict()
        return result
