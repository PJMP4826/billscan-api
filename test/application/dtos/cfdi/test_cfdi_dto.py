import json
import re
from pathlib import Path
from typing import get_type_hints

import pytest

from src.application.dtos.cfdi import (
    CfdiDto,
    CfdiRegistroFiscalDto,
    ComplementoDto,
    ConceptosDto,
    EmisorDto,
    ImpuestosDto,
    ReceptorDto,
    TimbreFiscalDigitalDto,
    TrasladoDto,
)
from src.infrastructure.adapters.cfdi_payload_mapper import to_canonical_payload

_FIXTURE = (
    Path(__file__).resolve().parents[3] / "fixtures" / "cfdi_ingreso_samples.json"
)
SAMPLES: list[dict] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
SAMPLE_IDS = [
    "muestra_nube",
    "muestra_gobierno",
    "muestra_comercio",
    "muestra_farmacia",
    "muestra_traslado_exento",
]


def _dto(sample: dict) -> CfdiDto:
    """Los fixtures tienen forma SAT; el adaptador los lleva a snake_case."""
    return CfdiDto.from_dict(to_canonical_payload(sample))


def _assert_snake_case_keys(
    node, parent_key: str | None = None, path: str = "$"
) -> None:
    if isinstance(node, dict):
        if parent_key != "traslados":
            for key in node:
                assert re.fullmatch(
                    r"[a-z][a-z0-9_]*", key
                ), f"key fuera de snake_case: {path}.{key}"
        for key, value in node.items():
            _assert_snake_case_keys(value, key, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _assert_snake_case_keys(item, parent_key, f"{path}[{index}]")


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_to_dict_uses_snake_case_keys(sample: dict) -> None:
    result = _dto(sample).to_dict()

    _assert_snake_case_keys(result)

    assert result["emisor"]["rfc"] == sample["Emisor"]["Rfc"]
    assert result["emisor"]["regimen_fiscal"] == sample["Emisor"]["RegimenFiscal"]
    assert result["receptor"]["uso_cfdi"] == sample["Receptor"]["UsoCFDI"]
    assert result["fecha"] == sample["Fecha"]
    assert result["sub_total"] == sample["SubTotal"]
    assert result["total"] == sample["Total"]
    assert (
        result["complemento"]["timbre_fiscal_digital"]["uuid"]
        == sample["Complemento"]["TimbreFiscalDigital"]["UUID"]
    )

    # Los opcionales siempre viajan en el dict; sin dato en el XML van en None.
    assert (result["impuestos"] is None) == ("Impuestos" not in sample)

    for snake_key, sat_key in (
        ("serie", "Serie"),
        ("folio", "Folio"),
        ("condiciones_de_pago", "CondicionesDePago"),
        ("tipo_cambio", "TipoCambio"),
        ("descuento", "Descuento"),
    ):
        assert result[snake_key] == sample.get(sat_key)

    for concepto, raw in zip(result["conceptos"], sample["Conceptos"]):
        assert concepto["clave_prod_serv"] == raw["ClaveProdServ"]
        assert (concepto["impuestos"] is None) == ("Impuestos" not in raw)


def test_from_dict_builds_nested_dto_objects() -> None:
    for sample in SAMPLES:
        dto = _dto(sample)
        assert isinstance(dto, CfdiDto)
        assert isinstance(dto.emisor, EmisorDto)
        assert isinstance(dto.receptor, ReceptorDto)
        assert isinstance(dto.complemento, ComplementoDto)
        assert isinstance(dto.complemento.timbre_fiscal_digital, TimbreFiscalDigitalDto)
        assert dto.conceptos
        for concepto in dto.conceptos:
            assert isinstance(concepto, ConceptosDto)
            if concepto.impuestos is not None:
                assert isinstance(concepto.impuestos, ImpuestosDto)
                for traslado in concepto.impuestos.traslados.values():
                    assert isinstance(traslado, TrasladoDto)
        if dto.impuestos is not None:
            assert isinstance(dto.impuestos, ImpuestosDto)
            for traslado in dto.impuestos.traslados.values():
                assert isinstance(traslado, TrasladoDto)
        registro = dto.complemento.cfdi_registro_fiscal
        if registro is not None:
            assert isinstance(registro, CfdiRegistroFiscalDto)


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_required_fields_are_mapped(sample: dict) -> None:
    dto = _dto(sample)

    assert dto.emisor.rfc == sample["Emisor"]["Rfc"]
    assert dto.emisor.nombre == sample["Emisor"]["Nombre"]
    assert dto.emisor.regimen_fiscal == sample["Emisor"]["RegimenFiscal"]
    assert dto.receptor.rfc == sample["Receptor"]["Rfc"]
    assert (
        dto.receptor.domicilio_fiscal_receptor
        == sample["Receptor"]["DomicilioFiscalReceptor"]
    )
    assert dto.receptor.uso_cfdi == sample["Receptor"]["UsoCFDI"]
    assert dto.version == sample["Version"]
    assert dto.fecha == sample["Fecha"]
    assert dto.forma_pago == sample["FormaPago"]
    assert dto.sub_total == sample["SubTotal"]
    assert dto.moneda == sample["Moneda"]
    assert dto.total == sample["Total"]
    assert dto.tipo_de_comprobante == sample["TipoDeComprobante"]
    assert dto.exportacion == sample["Exportacion"]
    assert dto.metodo_pago == sample["MetodoPago"]
    assert dto.lugar_expedicion == sample["LugarExpedicion"]
    assert (
        dto.complemento.timbre_fiscal_digital.uuid
        == sample["Complemento"]["TimbreFiscalDigital"]["UUID"]
    )
    assert (
        dto.complemento.timbre_fiscal_digital.fecha_timbrado
        == sample["Complemento"]["TimbreFiscalDigital"]["FechaTimbrado"]
    )

    assert len(dto.conceptos) == len(sample["Conceptos"])
    for concepto, raw in zip(dto.conceptos, sample["Conceptos"]):
        assert concepto.clave_prod_serv == raw["ClaveProdServ"]
        assert concepto.cantidad == raw["Cantidad"]
        assert concepto.clave_unidad == raw["ClaveUnidad"]
        assert concepto.descripcion == raw["Descripcion"]
        assert concepto.valor_unitario == raw["ValorUnitario"]
        assert concepto.importe == raw["Importe"]
        assert concepto.objeto_imp == raw["ObjetoImp"]


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_optional_fields_are_none_when_absent_in_source(sample: dict) -> None:
    dto = _dto(sample)

    assert dto.serie == sample.get("Serie")
    assert dto.folio == sample.get("Folio")
    assert dto.condiciones_de_pago == sample.get("CondicionesDePago")
    assert dto.tipo_cambio == sample.get("TipoCambio")
    assert dto.descuento == sample.get("Descuento")
    assert (dto.impuestos is not None) == ("Impuestos" in sample)
    assert (dto.complemento.cfdi_registro_fiscal is not None) == (
        "CFDIRegistroFiscal" in sample["Complemento"]
    )

    for concepto, raw in zip(dto.conceptos, sample["Conceptos"]):
        assert (concepto.impuestos is not None) == ("Impuestos" in raw)
        assert concepto.no_identificacion == raw.get("NoIdentificacion")
        assert concepto.unidad == raw.get("Unidad")
        assert concepto.descuento == raw.get("Descuento")


def test_sample_without_taxes_maps_all_tax_nodes_to_none() -> None:
    dto = _dto(SAMPLES[1])

    assert dto.impuestos is None
    assert dto.conceptos[0].impuestos is None
    assert dto.serie is None
    assert dto.folio is None
    assert dto.condiciones_de_pago is None
    assert dto.tipo_cambio is None
    assert dto.descuento is None
    assert dto.conceptos[0].no_identificacion == "OP-000123456"
    assert dto.complemento.cfdi_registro_fiscal is not None
    assert dto.complemento.cfdi_registro_fiscal.folio == "0000000000000001"


def test_tax_traslado_is_mapped_with_its_key() -> None:
    dto = _dto(SAMPLES[0])

    impuestos = dto.impuestos
    assert impuestos is not None
    assert impuestos.total_impuestos_trasladados == 200.0

    traslado = impuestos.traslados["002|Tasa|0.160000"]
    assert traslado.base == 1250.0
    assert traslado.impuesto == "002 - IVA"
    assert traslado.tipo_factor == "Tasa"
    assert traslado.tasa_o_cuota == 0.16
    assert traslado.importe == 200.0

    concepto_impuestos = dto.conceptos[0].impuestos
    assert concepto_impuestos is not None
    assert concepto_impuestos.total_impuestos_trasladados is None
    assert set(concepto_impuestos.traslados) == set(impuestos.traslados)


def test_exento_traslado_omits_tasa_and_importe() -> None:
    """CFDI 4.0: TipoFactor=Exento no trae TasaOCuota ni Importe."""
    sample = SAMPLES[4]
    dto = _dto(sample)

    impuestos = dto.impuestos
    assert impuestos is not None
    exento = impuestos.traslados["002|Exento"]
    assert exento.base == 250.44
    assert exento.impuesto == "002 - IVA"
    assert exento.tipo_factor == "Exento"
    assert exento.tasa_o_cuota is None
    assert exento.importe is None

    # El DTO conserva las claves y las expone en None (no las omite).
    assert exento.to_dict() == {
        "base": 250.44,
        "impuesto": "002 - IVA",
        "tipo_factor": "Exento",
        "tasa_o_cuota": None,
        "importe": None,
    }

    tasa = impuestos.traslados["002|Tasa|0.160000"]
    assert tasa.tasa_o_cuota == 0.16
    assert tasa.importe == 635.59
    assert impuestos.total_impuestos_trasladados == 635.59

    concepto_exento = dto.conceptos[1].impuestos
    assert concepto_exento is not None
    assert concepto_exento.traslados["002|Exento"].tasa_o_cuota is None


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_from_dict_round_trips_to_dict_output(sample: dict) -> None:
    """`cfdi_summary` se guarda con to_dict() y luego se hidrata de vuelta.

    Regresión: el detalle de cualquier CFDI nuevo fallaba con KeyError porque
    `from_dict` esperaba las claves SAT y la persistencia guarda snake_case.
    """
    dto = _dto(sample)
    serialized = dto.to_dict()

    restored = CfdiDto.from_dict(serialized)

    assert restored.emisor == dto.emisor
    assert restored.total == dto.total
    assert restored.to_dict() == serialized


def test_from_dict_rejects_pascal_case_payload() -> None:
    """El DTO solo habla snake_case; la traducción es del adaptador."""
    with pytest.raises(KeyError):
        CfdiDto.from_dict(SAMPLES[0])


def test_optional_and_required_type_annotations() -> None:
    cfdi_hints = get_type_hints(CfdiDto)
    assert cfdi_hints["emisor"] == EmisorDto
    assert cfdi_hints["conceptos"] == list[ConceptosDto]
    assert cfdi_hints["impuestos"] == ImpuestosDto | None
    assert cfdi_hints["serie"] == str | None
    assert cfdi_hints["folio"] == str | None
    assert cfdi_hints["condiciones_de_pago"] == str | None
    assert cfdi_hints["tipo_cambio"] == float | None
    assert cfdi_hints["descuento"] == float | None

    concepto_hints = get_type_hints(ConceptosDto)
    assert concepto_hints["impuestos"] == ImpuestosDto | None
    assert concepto_hints["no_identificacion"] == str | None
    assert concepto_hints["unidad"] == str | None
    assert concepto_hints["descuento"] == float | None
    assert concepto_hints["clave_prod_serv"] == str

    impuestos_hints = get_type_hints(ImpuestosDto)
    assert impuestos_hints["traslados"] == dict[str, TrasladoDto]
    assert impuestos_hints["total_impuestos_trasladados"] == float | None

    complemento_hints = get_type_hints(ComplementoDto)
    assert complemento_hints["timbre_fiscal_digital"] == TimbreFiscalDigitalDto
    assert complemento_hints["cfdi_registro_fiscal"] == CfdiRegistroFiscalDto | None
