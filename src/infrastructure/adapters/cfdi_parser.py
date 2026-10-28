from decimal import Decimal
from datetime import datetime, date
from typing import Any

from satcfdi.cfdi import CFDI  # type: ignore
from satcfdi.models.code import Code  # type: ignore

from src.application.dtos.cfdi import CfdiDto
from src.infrastructure.adapters.cfdi_payload_mapper import to_canonical_payload


class CfdiParser:
    """
    Service adapter para parsear contenido XML CFDI (SAT) desde bytes
    y retornar un CfdiDto tipado.
    """

    @staticmethod
    def parse_bytes(xml_content: bytes) -> CfdiDto:
        """
        Parsea el contenido XML de CFDI recibido como bytes.

        Args:
            xml_content (bytes): El contenido crudo del archivo XML CFDI.

        Returns:
            CfdiDto: Objeto tipado con los datos del CFDI de tipo Ingreso.
        """

        try:
            # 1. Decodificar bytes a string UTF-8
            xml_string = xml_content.decode("utf-8")

            # 2. Parsear con satcfdi
            cfdi_obj = CFDI.from_string(xml_string)  # type: ignore

            # 3. Convertir a diccionario y traducir al formato canónico.
            #    El mapper actúa como allowlist: descarta los campos sensibles
            #    del XML (Sello, Certificado, NoCertificado, SelloCFD...).
            factura_dict = to_canonical_payload(dict(cfdi_obj))  # type: ignore

            # 4. Convertir Decimal/date/Code a tipos serializables por JSON.
            factura_dict = CfdiParser._clean_dict_values(factura_dict)  # type: ignore

            tipo_comprobante = str(factura_dict.get("tipo_de_comprobante", ""))
            if not tipo_comprobante:
                raise ValueError("El CFDI no expone el atributo TipoDeComprobante.")
            if not tipo_comprobante.startswith("I"):
                raise ValueError(
                    "Solo se admiten CFDI de tipo Ingreso (I); "
                    f"se recibió '{tipo_comprobante}'."
                )

            return CfdiDto.from_dict(factura_dict)

        except UnicodeDecodeError:
            raise ValueError("El contenido XML no es válido UTF-8.")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error al parsear el XML CFDI: {e}")

    @staticmethod
    def _clean_dict_values(data: dict[str, Any]) -> dict[str, Any]:
        """Convierte tipos no nativos de JSON en el dict a tipos serializables."""
        return {k: CfdiParser._clean_value(v) for k, v in data.items()}

    @staticmethod
    def _clean_value(value: Any) -> Any:
        """Convierte un valor individual a tipo serializable por JSON."""
        if isinstance(value, dict):
            return {k: CfdiParser._clean_value(v) for k, v in value.items()}  # type: ignore[reportUnknownVariableType]
        if isinstance(value, list):
            return [CfdiParser._clean_value(item) for item in value]  # type: ignore
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Code):
            return str(value)
        return value
