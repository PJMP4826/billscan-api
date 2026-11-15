from __future__ import annotations

from typing import Final

from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.person_type import PersonType
from src.domain.enums.tax_regime import TaxRegime
from src.domain.errors.invoice_use_tax_regime_error import (
    InvalidInvoiceUseTaxRegimeCombinationError,
    InvoiceUseNotAllowedForPersonTypeError,
    InvoiceUseTaxRegimeError,
    TaxRegimeNotAllowedForPersonTypeError,
    UnknownInvoiceUseError,
    UnknownTaxRegimeError,
)


# ---------------------------------------------------------------------------
# c_RegimenFiscal -> tipo de persona al que aplica
# ---------------------------------------------------------------------------
_REGIMENES_PERSONA_FISICA: Final[frozenset[TaxRegime]] = frozenset(
    {
        TaxRegime.R605,
        TaxRegime.R606,
        TaxRegime.R607,
        TaxRegime.R608,
        TaxRegime.R610,
        TaxRegime.R611,
        TaxRegime.R612,
        TaxRegime.R614,
        TaxRegime.R615,
        TaxRegime.R616,
        TaxRegime.R621,
        TaxRegime.R625,
        TaxRegime.R626,
    }
)

_REGIMENES_PERSONA_MORAL: Final[frozenset[TaxRegime]] = frozenset(
    {
        TaxRegime.R601,
        TaxRegime.R603,
        TaxRegime.R610,
        TaxRegime.R620,
        TaxRegime.R622,
        TaxRegime.R623,
        TaxRegime.R624,
        TaxRegime.R626,
    }
)

_REGIMENES_VALIDOS: Final[frozenset[TaxRegime]] = (
    _REGIMENES_PERSONA_FISICA | _REGIMENES_PERSONA_MORAL
)

# ---------------------------------------------------------------------------
# Grupos de regímenes reutilizados por c_UsoCFDI
# ---------------------------------------------------------------------------
_REG_GENERAL: Final[frozenset[TaxRegime]] = frozenset(
    {
        TaxRegime.R601,
        TaxRegime.R603,
        TaxRegime.R606,
        TaxRegime.R612,
        TaxRegime.R620,
        TaxRegime.R621,
        TaxRegime.R622,
        TaxRegime.R623,
        TaxRegime.R624,
        TaxRegime.R625,
        TaxRegime.R626,
    }
)

_REG_G02: Final[frozenset[TaxRegime]] = _REG_GENERAL | {
    TaxRegime.R616
}

_REG_DEDUCCIONES_PF: Final[frozenset[TaxRegime]] = frozenset(
    {
        TaxRegime.R605,
        TaxRegime.R606,
        TaxRegime.R607,
        TaxRegime.R608,
        TaxRegime.R611,
        TaxRegime.R612,
        TaxRegime.R614,
        TaxRegime.R615,
        TaxRegime.R625,
    }
)

_REG_TODOS: Final[frozenset[TaxRegime]] = _REGIMENES_VALIDOS

# Los usos se derivan del enum para no repetir cada código.
_USOS_INVERSION: Final[frozenset[InvoiceUse]] = frozenset(
    uso for uso in InvoiceUse if uso.value.startswith("I")
)

_USOS_DEDUCCIONES: Final[frozenset[InvoiceUse]] = frozenset(
    uso for uso in InvoiceUse if uso.value.startswith("D")
)

# ---------------------------------------------------------------------------
# c_UsoCFDI -> regímenes fiscales receptores permitidos
# ---------------------------------------------------------------------------
_USO_CFDI_REGIMENES: Final[
    dict[InvoiceUse, frozenset[TaxRegime]]
] = {
    **{uso: _REG_GENERAL for uso in _USOS_INVERSION},
    **{uso: _REG_DEDUCCIONES_PF for uso in _USOS_DEDUCCIONES},
    InvoiceUse.G01: _REG_GENERAL,
    InvoiceUse.G02: _REG_G02,
    InvoiceUse.G03: _REG_GENERAL,
    InvoiceUse.S01: _REG_TODOS,
    InvoiceUse.CP01: _REG_TODOS,
    InvoiceUse.CN01: frozenset({TaxRegime.R605}),
}

# ---------------------------------------------------------------------------
# c_UsoCFDI -> tipos de persona a los que aplica
# ---------------------------------------------------------------------------
_USOS_SOLO_FISICA: Final[frozenset[InvoiceUse]] = (
    _USOS_DEDUCCIONES | {InvoiceUse.CN01}
)

_USO_CFDI_TIPO_PERSONA: Final[
    dict[InvoiceUse, frozenset[PersonType]]
] = {
    uso: (
        frozenset({PersonType.FISICA})
        if uso in _USOS_SOLO_FISICA
        else frozenset({PersonType.FISICA, PersonType.MORAL})
    )
    for uso in _USO_CFDI_REGIMENES
}

# Índice inverso: régimen -> usos permitidos (derivado, no se mantiene a mano)
_REGIMEN_USOS_CFDI: Final[
    dict[TaxRegime, frozenset[InvoiceUse]]
] = {
    regimen: frozenset(
        uso
        for uso, regimenes in _USO_CFDI_REGIMENES.items()
        if regimen in regimenes
    )
    for regimen in _REGIMENES_VALIDOS
}


class InvoiceUseTaxRegimeValidator:
    """Valida la combinación de UsoCFDI, régimen fiscal y tipo de persona."""

    def validate(
        self,
        uso_cfdi: InvoiceUse | str,
        regimen_fiscal: TaxRegime | str,
        tipo_persona: PersonType | None = None,
    ) -> None:
        """Lanza una excepción de dominio si la combinación no es válida."""
        uso = self._coerce_invoice_use(uso_cfdi)
        regimen = self._coerce_tax_regime(regimen_fiscal)

        if uso not in _USO_CFDI_REGIMENES:
            raise UnknownInvoiceUseError(uso.value)

        if regimen not in _REGIMENES_VALIDOS:
            raise UnknownTaxRegimeError(regimen.value)

        regimenes_permitidos = _USO_CFDI_REGIMENES[uso]
        if regimen not in regimenes_permitidos:
            raise InvalidInvoiceUseTaxRegimeCombinationError(
                uso.value,
                regimen.value,
                sorted(item.value for item in regimenes_permitidos),
            )

        if tipo_persona is None:
            return

        tipos_permitidos = _USO_CFDI_TIPO_PERSONA[uso]
        if tipo_persona not in tipos_permitidos:
            raise InvoiceUseNotAllowedForPersonTypeError(
                uso.value,
                tipo_persona.value,
                sorted(item.value for item in tipos_permitidos),
            )

        regimenes_persona = (
            _REGIMENES_PERSONA_FISICA
            if tipo_persona == PersonType.FISICA
            else _REGIMENES_PERSONA_MORAL
        )
        if regimen not in regimenes_persona:
            raise TaxRegimeNotAllowedForPersonTypeError(
                regimen.value,
                tipo_persona.value,
            )

    def is_valid(
        self,
        uso_cfdi: InvoiceUse | str,
        regimen_fiscal: TaxRegime | str,
        tipo_persona: PersonType | None = None,
    ) -> bool:
        """Devuelve ``True`` si la combinación es válida."""
        try:
            self.validate(uso_cfdi, regimen_fiscal, tipo_persona)
        except InvoiceUseTaxRegimeError:
            return False
        return True

    def allowed_regimes_for_use(
        self, uso_cfdi: InvoiceUse
    ) -> frozenset[TaxRegime]:
        """Regímenes permitidos para un uso de CFDI."""
        return _USO_CFDI_REGIMENES.get(uso_cfdi, frozenset())

    def allowed_uses_for_regime(
        self, regimen_fiscal: TaxRegime
    ) -> frozenset[InvoiceUse]:
        """Usos de CFDI permitidos para un régimen fiscal."""
        return _REGIMEN_USOS_CFDI.get(regimen_fiscal, frozenset())

    def allowed_person_types_for_use(
        self, uso_cfdi: InvoiceUse
    ) -> frozenset[PersonType]:
        """Tipos de persona permitidos para un uso de CFDI."""
        return _USO_CFDI_TIPO_PERSONA.get(uso_cfdi, frozenset())

    @staticmethod
    def _coerce_invoice_use(uso_cfdi: InvoiceUse | str) -> InvoiceUse:
        if isinstance(uso_cfdi, InvoiceUse):
            return uso_cfdi

        try:
            return InvoiceUse(uso_cfdi.strip().upper())
        except ValueError as exc:
            raise UnknownInvoiceUseError(uso_cfdi) from exc

    @staticmethod
    def _coerce_tax_regime(
        regimen_fiscal: TaxRegime | str,
    ) -> TaxRegime:
        if isinstance(regimen_fiscal, TaxRegime):
            return regimen_fiscal

        try:
            return TaxRegime(regimen_fiscal.strip())
        except ValueError as exc:
            raise UnknownTaxRegimeError(regimen_fiscal) from exc
