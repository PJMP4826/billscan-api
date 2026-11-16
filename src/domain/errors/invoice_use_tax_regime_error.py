from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BadRequestError


class InvoiceUseTaxRegimeError(BadRequestError):
    """Combinación inválida de UsoCFDI, régimen fiscal y tipo de persona."""

    default_error_code = "INVALID_INVOICE_USE_TAX_REGIME"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )


class UnknownInvoiceUseError(InvoiceUseTaxRegimeError):
    def __init__(self, uso_cfdi: str) -> None:
        super().__init__(
            f"UsoCFDI '{uso_cfdi}' no existe en c_UsoCFDI o no está soportado.",
            error_code="UNKNOWN_INVOICE_USE",
            details={"uso_cfdi": uso_cfdi},
        )


class UnknownTaxRegimeError(InvoiceUseTaxRegimeError):
    def __init__(self, regimen_fiscal: str) -> None:
        super().__init__(
            f"RegimenFiscal '{regimen_fiscal}' no existe en c_RegimenFiscal "
            "o no está soportado.",
            error_code="UNKNOWN_TAX_REGIME",
            details={"regimen_fiscal": regimen_fiscal},
        )


class InvalidInvoiceUseTaxRegimeCombinationError(InvoiceUseTaxRegimeError):
    def __init__(
        self,
        uso_cfdi: str,
        regimen_fiscal: str,
        allowed_regimes: list[str],
    ) -> None:
        super().__init__(
            f"El UsoCFDI '{uso_cfdi}' no es válido para el régimen {regimen_fiscal}",
            error_code="INVOICE_USE_TAX_REGIME_MISMATCH",
            details={
                "uso_cfdi": uso_cfdi,
                "regimen_fiscal": regimen_fiscal,
                "allowed_regimes": allowed_regimes,
            },
        )


class NoRegisteredRegimenAllowsInvoiceUseError(InvoiceUseTaxRegimeError):
    def __init__(
        self,
        uso_cfdi: str,
        registered_regimes: list[str],
        allowed_regimes: list[str],
    ) -> None:
        super().__init__(
            f"Ninguno de los regímenes registrados del usuario permite el "
            f"UsoCFDI '{uso_cfdi}'. Regímenes registrados: "
            f"{', '.join(registered_regimes)}. Regímenes permitidos: "
            f"{', '.join(allowed_regimes)}.",
            error_code="INVOICE_USE_NO_COMPATIBLE_REGIMEN",
            details={
                "uso_cfdi": uso_cfdi,
                "registered_regimes": registered_regimes,
                "allowed_regimes": allowed_regimes,
            },
        )


class InvoiceUseNotAllowedForPersonTypeError(InvoiceUseTaxRegimeError):
    def __init__(
        self,
        uso_cfdi: str,
        tipo_persona: str,
        allowed_person_types: list[str],
    ) -> None:
        super().__init__(
            f"El UsoCFDI '{uso_cfdi}' no aplica para persona "
            f"{tipo_persona.lower()}. Tipos de persona permitidos: "
            f"{', '.join(allowed_person_types)}.",
            error_code="INVOICE_USE_PERSON_TYPE_MISMATCH",
            details={
                "uso_cfdi": uso_cfdi,
                "tipo_persona": tipo_persona,
                "allowed_person_types": allowed_person_types,
            },
        )


class TaxRegimeNotAllowedForPersonTypeError(InvoiceUseTaxRegimeError):
    def __init__(
        self,
        regimen_fiscal: str,
        tipo_persona: str,
    ) -> None:
        super().__init__(
            f"El régimen '{regimen_fiscal}' no aplica para persona "
            f"{tipo_persona.lower()}.",
            error_code="TAX_REGIME_PERSON_TYPE_MISMATCH",
            details={
                "regimen_fiscal": regimen_fiscal,
                "tipo_persona": tipo_persona,
            },
        )
