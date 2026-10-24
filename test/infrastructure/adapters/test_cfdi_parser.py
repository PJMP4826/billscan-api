import copy
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from src.application.dtos.cfdi import CfdiDto
from src.infrastructure.adapters.cfdi_parser import CfdiParser

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "cfdi_ingreso_samples.json"
)
SAMPLES: list[dict] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
SAMPLE_IDS = [
    "muestra_nube",
    "muestra_gobierno",
    "muestra_comercio",
    "muestra_farmacia",
    "muestra_traslado_exento",
]

_PARSE_TARGET = "src.infrastructure.adapters.cfdi_parser.CFDI.from_string"


def _raw_cfdi(sample: dict) -> dict:
    """Simula el dict crudo previo a la limpieza (con sellos y tipos nativos)."""
    raw = copy.deepcopy(sample)
    raw["Certificado"] = "AAA..."
    raw["NoCertificado"] = "00000000000000030000"
    raw["Sello"] = "SELO_CRUDO"
    raw["SubTotal"] = Decimal(str(raw["SubTotal"]))
    raw["Fecha"] = datetime.fromisoformat(raw["Fecha"])
    tfd = raw["Complemento"]["TimbreFiscalDigital"]
    tfd["SelloCFD"] = "sello_cfd"
    tfd["SelloSAT"] = "sello_sat"
    tfd["NoCertificadoSAT"] = "00000000000000000000"
    return raw


def _collect_keys(node) -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(str(key).lower())
            keys |= _collect_keys(value)
    elif isinstance(node, list):
        for item in node:
            keys |= _collect_keys(item)
    return keys


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_parse_bytes_returns_typed_cfdi_dto(sample: dict) -> None:
    raw = _raw_cfdi(sample)
    with patch(_PARSE_TARGET, side_effect=lambda *_a, **_k: copy.deepcopy(raw)):
        dto = CfdiParser.parse_bytes(b"<xml/>")

    assert isinstance(dto, CfdiDto)
    assert dto.emisor.nombre == sample["Emisor"]["Nombre"]
    assert dto.total == sample["Total"]

    result = dto.to_dict()
    assert result["emisor"]["rfc"] == sample["Emisor"]["Rfc"]
    assert result["total"] == sample["Total"]
    # Los opcionales siempre están presentes; sin dato en el XML valen None.
    assert result["serie"] == sample.get("Serie")


def test_parse_bytes_strips_sensitive_fields() -> None:
    raw = _raw_cfdi(SAMPLES[0])
    with patch(_PARSE_TARGET, side_effect=lambda *_a, **_k: copy.deepcopy(raw)):
        result = CfdiParser.parse_bytes(b"<xml/>").to_dict()

    keys = _collect_keys(result)
    assert not any("sello" in key for key in keys), keys
    assert not any("certificado" in key for key in keys), keys


def test_parse_bytes_converts_decimals_and_datetimes() -> None:
    sample = SAMPLES[0]
    raw = _raw_cfdi(sample)
    assert isinstance(raw["SubTotal"], Decimal)
    assert isinstance(raw["Fecha"], datetime)

    with patch(_PARSE_TARGET, side_effect=lambda *_a, **_k: copy.deepcopy(raw)):
        dto = CfdiParser.parse_bytes(b"<xml/>")

    assert isinstance(dto.sub_total, float)
    assert dto.sub_total == sample["SubTotal"]
    assert isinstance(dto.fecha, str)
    assert dto.fecha == sample["Fecha"]
    assert isinstance(dto.conceptos[0].cantidad, float)
    assert dto.conceptos[0].cantidad == sample["Conceptos"][0]["Cantidad"]


def test_parse_bytes_rejects_non_income_cfdi() -> None:
    raw = _raw_cfdi(SAMPLES[0])
    raw["TipoDeComprobante"] = "E - Egreso"

    with patch(_PARSE_TARGET, side_effect=lambda *_a, **_k: copy.deepcopy(raw)):
        with pytest.raises(ValueError, match="Solo se admiten CFDI de tipo Ingreso"):
            CfdiParser.parse_bytes(b"<xml/>")


def test_parse_bytes_rejects_invalid_utf8() -> None:
    with pytest.raises(ValueError, match="UTF-8"):
        CfdiParser.parse_bytes(b"\xff\xfe")


def test_parse_bytes_wraps_satcfdi_errors() -> None:
    with patch(_PARSE_TARGET, side_effect=Exception("xml corrupto")):
        with pytest.raises(
            ValueError, match="Error al parsear el XML CFDI: xml corrupto"
        ):
            CfdiParser.parse_bytes(b"<xml/>")


def test_parse_bytes_wraps_missing_required_field() -> None:
    raw = _raw_cfdi(SAMPLES[0])
    del raw["Emisor"]

    with patch(_PARSE_TARGET, side_effect=lambda *_a, **_k: copy.deepcopy(raw)):
        with pytest.raises(ValueError, match="Error al parsear el XML CFDI"):
            CfdiParser.parse_bytes(b"<xml/>")
