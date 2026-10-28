"""Traducción del payload SAT (PascalCase) al formato canónico del dominio.

``satcfdi`` entrega los atributos del CFDI tal como aparecen en el XML del SAT:
``Emisor``, ``SubTotal``, ``TipoDeComprobante``... Los DTOs de aplicación, en
cambio, trabajan en ``snake_case``, y ese mismo formato es el que se persiste
en ``receipt_billing_details.cfdi_summary``.

Esta traducción vive aquí, en el adaptador de infraestructura, para que el
resto del sistema maneje **un único formato** y los DTOs no tengan que conocer
las dos convenciones.

El mapeo es una lista explícita (no una heurística de camel→snake) porque los
acrónimos del SAT rompen cualquier conversión automática:
``UsoCFDI``, ``TasaOCuota``, ``RfcProvCertif``, ``ObjetoImp``.

.. note::
   La tabla funciona como **allowlist**: toda clave que no aparezca aquí se
   descarta. Eso elimina los datos sensibles del CFDI (``Sello``,
   ``Certificado``, ``NoCertificado``, ``SelloCFD``, ``SelloSAT``...) sin
   necesidad de mantener una denylist aparte.
"""

from typing import Any, Final

#: Claves del XML del SAT → nombres canónicos usados por los DTOs.
SAT_TO_CANONICAL: Final[dict[str, str]] = {
    # Nodo raíz
    "Version": "version",
    "Serie": "serie",
    "Folio": "folio",
    "Fecha": "fecha",
    "FormaPago": "forma_pago",
    "CondicionesDePago": "condiciones_de_pago",
    "SubTotal": "sub_total",
    "Descuento": "descuento",
    "Moneda": "moneda",
    "TipoCambio": "tipo_cambio",
    "Total": "total",
    "TipoDeComprobante": "tipo_de_comprobante",
    "Exportacion": "exportacion",
    "MetodoPago": "metodo_pago",
    "LugarExpedicion": "lugar_expedicion",
    # Nodos contenedores
    "Emisor": "emisor",
    "Receptor": "receptor",
    "Conceptos": "conceptos",
    "Impuestos": "impuestos",
    "Traslados": "traslados",
    "Complemento": "complemento",
    "TimbreFiscalDigital": "timbre_fiscal_digital",
    "CFDIRegistroFiscal": "cfdi_registro_fiscal",
    # Emisor / Receptor
    "Rfc": "rfc",
    "Nombre": "nombre",
    "RegimenFiscal": "regimen_fiscal",
    "DomicilioFiscalReceptor": "domicilio_fiscal_receptor",
    "RegimenFiscalReceptor": "regimen_fiscal_receptor",
    "UsoCFDI": "uso_cfdi",
    # Conceptos
    "ClaveProdServ": "clave_prod_serv",
    "NoIdentificacion": "no_identificacion",
    "Cantidad": "cantidad",
    "ClaveUnidad": "clave_unidad",
    "Unidad": "unidad",
    "Descripcion": "descripcion",
    "ValorUnitario": "valor_unitario",
    "Importe": "importe",
    "ObjetoImp": "objeto_imp",
    # Impuestos / Traslados
    "Base": "base",
    "Impuesto": "impuesto",
    "TipoFactor": "tipo_factor",
    "TasaOCuota": "tasa_o_cuota",
    "TotalImpuestosTrasladados": "total_impuestos_trasladados",
    # Complemento / TimbreFiscalDigital
    "UUID": "uuid",
    "FechaTimbrado": "fecha_timbrado",
    "RfcProvCertif": "rfc_prov_certif",
}

#: Nodos cuyo contenido es un mapa indexado por una clave del SAT
#: (``"002|Tasa|0.160000"``) en lugar de un objeto con atributos. Esas claves
#: se conservan tal cual; solo se traducen los atributos de cada valor.
_OPAQUE_MAP_KEYS: Final[frozenset[str]] = frozenset({"traslados"})


def to_canonical_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Convierte un payload del SAT a ``snake_case``, recursivamente.

    Args:
        data: Diccionario tal como lo entrega ``satcfdi`` (claves PascalCase).

    Returns:
        Diccionario nuevo con claves canónicas. Las claves desconocidas se
        descartan, lo que también elimina los campos sensibles del XML.
    """
    return _convert(data, parent_key=None)


def _convert(node: Any, parent_key: str | None) -> Any:
    if isinstance(node, dict):
        if parent_key in _OPAQUE_MAP_KEYS:
            return {
                str(key): _convert(value, parent_key=None) # type: ignore
                for key, value in node.items() # type: ignore
            }
        return {
            canonical: _convert(value, parent_key=canonical)
            for key, value in node.items() # type: ignore
            if (canonical := SAT_TO_CANONICAL.get(key)) is not None # type: ignore
        }
    if isinstance(node, list):
        return [_convert(item, parent_key=parent_key) for item in node] # type: ignore
    return node
