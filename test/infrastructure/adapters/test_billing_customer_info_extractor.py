import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from csf_scraper import CsfImageExtractor, PersonaFisica, PersonaMoral, Regimen
from csf_scraper.value_objects import Rfc

from src.domain.enums.tax_regime import TaxRegime
from src.infrastructure.adapters.billing_customer_info_extractor import (
    BillingCustomerInfoExtractor,
)
from src.shared.errors.base_exception import BadRequestError

_PDF_BYTES = b"%PDF-1.4\n%fake\n"
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
_JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 8

_SCRAPER_TARGET = "src.infrastructure.adapters.billing_customer_info_extractor.Scraper"


class _FakeImageReader:
    """Motor de lectura falso: el adaptador solo lo envuelve, no lo invoca."""

    async def read(self, image: Any) -> Any:  # pragma: no cover - no se usa
        raise AssertionError("read() no debe llamarse en estos tests")


def _make_fake_scraper(person: PersonaMoral | PersonaFisica) -> type:
    """Devuelve una clase con la misma superficie que usa el adaptador."""

    class _FakeScraper:
        calls: list[str] = []
        created_kwargs: dict[str, Any] = {}

        @classmethod
        def create(cls, **kwargs: Any) -> "_FakeScraper":
            cls.created_kwargs = kwargs
            cls.calls = []
            return cls()

        async def __aenter__(self) -> "_FakeScraper":
            return self

        async def __aexit__(self, *exc_info: Any) -> None:
            return None

        async def obtain_from_pdf_path(self, path: str) -> Any:
            assert path.endswith(".pdf")
            type(self).calls.append("pdf")
            return person

        async def obtain_from_image_path(self, path: str) -> Any:
            assert path.endswith((".jpg", ".png"))
            type(self).calls.append("image")
            return person

    return _FakeScraper


def _moral(*regimenes: Regimen) -> PersonaMoral:
    return PersonaMoral(
        razon_social="ACME SA DE CV",
        rfc=Rfc("ACM010101AAA"),
        correo_electronico="facturas@acme.mx",
        codigo_postal="06600",
        tipo_vialidad="CALLE",
        nombre_vialidad="REFORMA",
        numero_exterior="222",
        colonia="JUAREZ",
        municipio_delegacion="CUAUHTEMOC",
        entidad_federativa="CIUDAD DE MEXICO",
        regimenes=list(regimenes),
    )


def _fisica() -> PersonaFisica:
    return PersonaFisica(
        nombre="JUAN CARLOS",
        apellido_paterno="PEREZ",
        apellido_materno="LOPEZ",
        rfc=Rfc("PELJ900101XXX"),
        regimenes=[
            Regimen(
                regimen="Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios"
            )
        ],
    )


def _extractor() -> BillingCustomerInfoExtractor:
    return BillingCustomerInfoExtractor(image_reader=_FakeImageReader())  # type: ignore[arg-type]


def _run_extract(
    person: PersonaMoral | PersonaFisica, content: bytes, mime_type: str
) -> tuple[Any, Any]:
    fake = _make_fake_scraper(person)
    with patch(_SCRAPER_TARGET, fake):
        dto = asyncio.run(_extractor().extract(content, mime_type))
    return dto, fake


def test_wraps_image_reader_with_csf_image_extractor() -> None:
    assert isinstance(_extractor()._image_extractor, CsfImageExtractor)


@pytest.mark.parametrize(
    ("content", "mime_type", "expected"),
    [
        (_PDF_BYTES, "application/octet-stream", "application/pdf"),
        (_PDF_BYTES, "application/pdf; charset=binary", "application/pdf"),
        (_PNG_BYTES, "image/jpg", "image/png"),
        (_JPEG_BYTES, "", "image/jpeg"),
        (_JPEG_BYTES, "image/jpg", "image/jpeg"),
        (_JPEG_BYTES, "image/pjpeg", "image/jpeg"),
    ],
)
def test_detect_kind_prefers_magic_bytes(
    content: bytes, mime_type: str, expected: str
) -> None:
    assert _extractor()._detect_kind(content, mime_type) == expected


@pytest.mark.parametrize(
    ("mime_type", "expected"),
    [
        ("image/jpg", "image/jpeg"),
        ("image/JPEG; charset=binary", "image/jpeg"),
        ("image/pjpeg", "image/jpeg"),
        ("image/jfif", "image/jpeg"),
        ("image/x-png", "image/png"),
        ("application/pdf", "application/pdf"),
    ],
)
def test_normalize_mime_resolves_aliases(mime_type: str, expected: str) -> None:
    assert _extractor()._normalize_mime(mime_type) == expected


@pytest.mark.parametrize("mime_type", ["image/jpeg", "image/jpg", "image/pjpeg"])
def test_jpg_and_jpeg_share_the_image_strategy(mime_type: str) -> None:
    extractor = _extractor()
    suffix, reader = extractor._readers[extractor._detect_kind(_JPEG_BYTES, mime_type)]

    assert suffix == "jpg"
    assert reader.__func__ is BillingCustomerInfoExtractor._read_image


def test_detect_kind_rejects_unsupported_content() -> None:
    with pytest.raises(BadRequestError) as raised:
        _extractor()._detect_kind(b"hola mundo", "text/plain")

    assert raised.value.error_code == "UNSUPPORTED_CSF_FORMAT"


def test_map_regimens_keeps_all_in_sat_order() -> None:
    person = _moral(
        Regimen(
            regimen="Régimen General de Ley Personas Morales", fecha_alta="01-01-2020"
        ),
        Regimen(regimen="Régimen Simplificado de Confianza", fecha_alta="05-06-2022"),
    )

    assert [r.code for r in _extractor()._map_regimens(person.regimenes)] == [
        TaxRegime.R601,
        TaxRegime.R626,
    ]


def test_map_regimens_without_regimenes_raises() -> None:
    with pytest.raises(BadRequestError) as raised:
        _extractor()._map_regimens([])

    assert raised.value.error_code == "CSF_NO_REGIMEN"


def test_map_regimens_skips_unknown_but_keeps_known() -> None:
    person = _moral(
        Regimen(regimen="Régimen inventado"),
        Regimen(regimen="Régimen General de Ley Personas Morales"),
    )

    assert [r.code for r in _extractor()._map_regimens(person.regimenes)] == [
        TaxRegime.R601
    ]


def test_map_regimens_raises_when_none_is_supported() -> None:
    with pytest.raises(BadRequestError) as raised:
        _extractor()._map_regimens([Regimen(regimen="Régimen inventado")])

    assert raised.value.error_code == "CSF_UNSUPPORTED_REGIMEN"


def test_resolve_tax_regime_falls_back_to_description() -> None:
    # ``615`` no existe en el catálogo interno de ``csf_scraper``.
    regimen = Regimen(regimen="Régimen de los ingresos por obtención de premios")

    assert _extractor()._resolve_tax_regime(regimen) is TaxRegime.R615


def test_resolve_tax_regime_returns_none_for_unknown_regimen() -> None:
    assert (
        _extractor()._resolve_tax_regime(Regimen(regimen="Régimen inventado")) is None
    )


def test_to_dto_builds_moral_payload() -> None:
    dto = _extractor()._to_dto(
        _moral(Regimen(regimen="Régimen General de Ley Personas Morales"))
    )

    assert dto.razon_social == "ACME SA DE CV"
    assert dto.rfc == "ACM010101AAA"
    assert [r.code for r in dto.regimens] == [TaxRegime.R601]
    assert dto.cp == "06600"
    assert "CALLE REFORMA" in (dto.address or "")
    assert "C.P. 06600" in (dto.address or "")
    assert dto.primary_regimen is TaxRegime.R601
    assert not dto.needs_regimen_selection

    billing = dto.to_billing_customer(email="facturas@acme.mx")
    assert billing.email == "facturas@acme.mx"
    assert billing.regimen is TaxRegime.R601


def test_to_dto_builds_fisica_payload_with_full_name() -> None:
    dto = _extractor()._to_dto(_fisica())

    assert dto.razon_social == "JUAN CARLOS PEREZ LOPEZ"
    assert [r.code for r in dto.regimens] == [TaxRegime.R605]


def test_to_dto_exposes_multiple_regimens_without_choosing() -> None:
    dto = _extractor()._to_dto(
        _moral(
            Regimen(regimen="Régimen General de Ley Personas Morales"),
            Regimen(regimen="Régimen Simplificado de Confianza"),
        )
    )

    assert dto.primary_regimen is None
    assert dto.needs_regimen_selection
    with pytest.raises(ValueError):
        dto.to_billing_customer(email="facturas@acme.mx")
    chosen = dto.to_billing_customer(email="facturas@acme.mx", regimen=TaxRegime.R626)
    assert chosen.regimen is TaxRegime.R626


def test_extract_reads_pdf_through_pdf_path() -> None:
    dto, fake = _run_extract(
        _moral(Regimen(regimen="Régimen General de Ley Personas Morales")),
        _PDF_BYTES,
        "application/pdf",
    )

    assert dto.rfc == "ACM010101AAA"
    assert fake.calls == ["pdf"]
    assert isinstance(fake.created_kwargs["image_extractor"], CsfImageExtractor)


def test_extract_reads_image_through_image_path() -> None:
    dto, fake = _run_extract(
        _moral(Regimen(regimen="Régimen Simplificado de Confianza")),
        _PNG_BYTES,
        "image/png",
    )

    assert [r.code for r in dto.regimens] == [TaxRegime.R626]
    assert fake.calls == ["image"]


def test_extract_rejects_unsupported_format() -> None:
    with pytest.raises(BadRequestError) as raised:
        asyncio.run(_extractor().extract(b"hola mundo", "text/plain"))

    assert raised.value.error_code == "UNSUPPORTED_CSF_FORMAT"
