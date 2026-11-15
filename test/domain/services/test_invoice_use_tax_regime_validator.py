import pytest

from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.person_type import PersonType
from src.domain.enums.tax_regime import TaxRegime
from src.domain.errors.invoice_use_tax_regime_error import (
    InvalidInvoiceUseTaxRegimeCombinationError,
    InvoiceUseNotAllowedForPersonTypeError,
    TaxRegimeNotAllowedForPersonTypeError,
    UnknownInvoiceUseError,
    UnknownTaxRegimeError,
)
from src.domain.services.invoice_use_tax_regime_validator import (
    InvoiceUseTaxRegimeValidator,
)


@pytest.fixture
def validator() -> InvoiceUseTaxRegimeValidator:
    return InvoiceUseTaxRegimeValidator()


@pytest.mark.parametrize(
    ("uso_cfdi", "regimen_fiscal", "tipo_persona"),
    [
        (InvoiceUse.G01, TaxRegime.R601, None),
        (InvoiceUse.G01, TaxRegime.R601, PersonType.MORAL),
        (InvoiceUse.G03, TaxRegime.R612, PersonType.FISICA),
        (InvoiceUse.G02, TaxRegime.R616, PersonType.FISICA),
        (InvoiceUse.D01, TaxRegime.R612, PersonType.FISICA),
        (InvoiceUse.S01, TaxRegime.R605, None),
        (InvoiceUse.S01, TaxRegime.R601, PersonType.MORAL),
        (InvoiceUse.CP01, TaxRegime.R601, PersonType.MORAL),
        (InvoiceUse.CN01, TaxRegime.R605, PersonType.FISICA),
    ],
)
def test_is_valid_accepts_valid_combinations(
    validator: InvoiceUseTaxRegimeValidator,
    uso_cfdi: InvoiceUse,
    regimen_fiscal: TaxRegime,
    tipo_persona: PersonType | None,
) -> None:
    assert validator.is_valid(uso_cfdi, regimen_fiscal, tipo_persona) is True


def test_validate_accepts_string_codes(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    assert validator.validate("g01", "601") is None
    assert validator.is_valid("G03", "601", PersonType.MORAL) is True


@pytest.mark.parametrize("uso_cfdi", ["P01", InvoiceUse.P01])
def test_unsupported_invoice_use_raises(
    validator: InvoiceUseTaxRegimeValidator,
    uso_cfdi: str | InvoiceUse,
) -> None:
    with pytest.raises(UnknownInvoiceUseError) as exc_info:
        validator.validate(uso_cfdi, TaxRegime.R601)

    assert exc_info.value.error_code == "UNKNOWN_INVOICE_USE"
    assert exc_info.value.details["uso_cfdi"] == "P01"


@pytest.mark.parametrize(
    "regimen_fiscal",
    [TaxRegime.R609, TaxRegime.R628, TaxRegime.R629, TaxRegime.R630],
)
def test_unsupported_tax_regime_raises(
    validator: InvoiceUseTaxRegimeValidator,
    regimen_fiscal: TaxRegime,
) -> None:
    with pytest.raises(UnknownTaxRegimeError) as exc_info:
        validator.validate(InvoiceUse.G03, regimen_fiscal)

    assert exc_info.value.error_code == "UNKNOWN_TAX_REGIME"
    assert exc_info.value.details["regimen_fiscal"] == regimen_fiscal.value


@pytest.mark.parametrize(
    ("uso_cfdi", "regimen_fiscal"),
    [
        ("ZZZ", "601"),
        (InvoiceUse.G03, "999"),
    ],
)
def test_unknown_string_codes_raise(
    validator: InvoiceUseTaxRegimeValidator,
    uso_cfdi: str,
    regimen_fiscal: str,
) -> None:
    expected_error = (
        UnknownInvoiceUseError
        if uso_cfdi == "ZZZ"
        else UnknownTaxRegimeError
    )

    with pytest.raises(expected_error):
        validator.validate(uso_cfdi, regimen_fiscal)


@pytest.mark.parametrize(
    ("uso_cfdi", "regimen_fiscal"),
    [
        (InvoiceUse.D01, TaxRegime.R601),
        (InvoiceUse.CN01, TaxRegime.R601),
        (InvoiceUse.G01, TaxRegime.R605),
    ],
)
def test_invalid_use_and_regime_combination_raises(
    validator: InvoiceUseTaxRegimeValidator,
    uso_cfdi: InvoiceUse,
    regimen_fiscal: TaxRegime,
) -> None:
    with pytest.raises(InvalidInvoiceUseTaxRegimeCombinationError) as exc_info:
        validator.validate(uso_cfdi, regimen_fiscal)

    error = exc_info.value
    assert error.error_code == "INVOICE_USE_TAX_REGIME_MISMATCH"
    assert error.details["uso_cfdi"] == uso_cfdi.value
    assert error.details["regimen_fiscal"] == regimen_fiscal.value
    assert error.details["allowed_regimes"] == sorted(
        item.value
        for item in validator.allowed_regimes_for_use(uso_cfdi)
    )


def test_use_not_allowed_for_person_type_raises(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    with pytest.raises(InvoiceUseNotAllowedForPersonTypeError) as exc_info:
        validator.validate(InvoiceUse.D01, TaxRegime.R612, PersonType.MORAL)

    error = exc_info.value
    assert error.error_code == "INVOICE_USE_PERSON_TYPE_MISMATCH"
    assert error.details["uso_cfdi"] == "D01"
    assert error.details["tipo_persona"] == "MORAL"
    assert error.details["allowed_person_types"] == ["FISICA"]


def test_tax_regime_not_allowed_for_person_type_raises(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    with pytest.raises(TaxRegimeNotAllowedForPersonTypeError) as exc_info:
        validator.validate(InvoiceUse.G01, TaxRegime.R601, PersonType.FISICA)

    error = exc_info.value
    assert error.error_code == "TAX_REGIME_PERSON_TYPE_MISMATCH"
    assert error.details["regimen_fiscal"] == "601"
    assert error.details["tipo_persona"] == "FISICA"


def test_allowed_regimes_for_use(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    allowed = validator.allowed_regimes_for_use(InvoiceUse.G01)

    assert TaxRegime.R601 in allowed
    assert TaxRegime.R605 not in allowed
    assert len(allowed) == 11
    assert validator.allowed_regimes_for_use(InvoiceUse.P01) == frozenset()


def test_allowed_uses_for_regime(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    allowed = validator.allowed_uses_for_regime(TaxRegime.R605)

    assert InvoiceUse.D01 in allowed
    assert InvoiceUse.CN01 in allowed
    assert InvoiceUse.S01 in allowed
    assert InvoiceUse.CP01 in allowed
    assert InvoiceUse.G01 not in allowed
    assert (
        validator.allowed_uses_for_regime(TaxRegime.R628) == frozenset()
    )


def test_allowed_person_types_for_use(
    validator: InvoiceUseTaxRegimeValidator,
) -> None:
    assert validator.allowed_person_types_for_use(InvoiceUse.CN01) == (
        frozenset({PersonType.FISICA})
    )
    assert validator.allowed_person_types_for_use(InvoiceUse.G01) == (
        frozenset({PersonType.FISICA, PersonType.MORAL})
    )


@pytest.mark.parametrize(
    ("rfc", "expected"),
    [
        ("ACM010101AAA", PersonType.MORAL),
        ("AACM010101AAA", PersonType.FISICA),
        ("  ACM010101AAA  ", PersonType.MORAL),
    ],
)
def test_person_type_from_rfc(
    rfc: str,
    expected: PersonType,
) -> None:
    assert PersonType.from_rfc(rfc) == expected


@pytest.mark.parametrize("rfc", ["", "ACM010101AA", "AACM010101AAAA"])
def test_person_type_from_invalid_rfc_raises(rfc: str) -> None:
    with pytest.raises(ValueError):
        PersonType.from_rfc(rfc)
