from decimal import Decimal
from datetime import datetime, date
from typing import Any

from satcfdi.cfdi import CFDI  # type: ignore
from satcfdi.models.code import Code  # type: ignore


class CfdiParser:
    """
    Service adapter para parsear contenido XML CFDI (SAT) desde bytes
    y retornar un diccionario limpio serializable.
    """

    @staticmethod
    def parse_bytes(xml_content: bytes) -> dict[str, Any]:
        """
        Parsea el contenido XML de CFDI recibido como bytes.

        Args:
            xml_content (bytes): El contenido crudo del archivo XML CFDI.

        Returns:
            Dict[str, Any]: Diccionario con los datos de la factura limpios.
        """

        try:
            # 1. Decodificar bytes a string UTF-8
            xml_string = xml_content.decode("utf-8")

            # 2. Parsear con satcfdi
            cfdi_obj = CFDI.from_string(xml_string)  # type: ignore

            # 3. Convertir a diccionario
            factura_dict = dict(cfdi_obj)  # type: ignore

            # 4. Limpieza de campos sensibles
            # Eliminar campos del nodo principal
            factura_dict.pop("Certificado", None)  # type: ignore
            factura_dict.pop("NoCertificado", None)  # type: ignore
            factura_dict.pop("Sello", None)  # type: ignore

            # Eliminar campos dentro del Complemento (TimbreFiscalDigital)
            if (
                "Complemento" in factura_dict
                and "TimbreFiscalDigital" in factura_dict["Complemento"]
            ):
                tfd = factura_dict["Complemento"]["TimbreFiscalDigital"]  # type: ignore
                tfd.pop("SelloCFD", None)  # type: ignore
                tfd.pop("SelloSAT", None)  # type: ignore
                tfd.pop("NoCertificadoSAT", None)  # type: ignore

            # Nota: El dict ya tiene tipos manejables tras la limpieza,
            # pero esto asegura consistencia si hay Decimal o fechas anidadas.
            factura_dict = CfdiParser._clean_dict_values(factura_dict)  # type: ignore

            return factura_dict

        except UnicodeDecodeError:
            raise ValueError("El contenido XML no es válido UTF-8.")
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
