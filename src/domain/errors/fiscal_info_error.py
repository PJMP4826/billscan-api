from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BadRequestError, NotFoundError


class FiscalInfoNotFoundError(NotFoundError):
    default_error_code = "FISCAL_INFO_NOT_FOUND"

    def __init__(
        self,
        message: str = "No hay informacion fiscal asociada a tu usuario",
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )


class FiscalInfoRequiredError(BadRequestError):
    default_error_code = "FISCAL_INFO_REQUIRED"

    def __init__(
        self,
        message: str = (
            "No hay informacion fiscal asociada a tu usuario. "
            "Registra tu informacion fiscal antes de facturar."
        ),
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )


class InvalidFiscalDataError(BadRequestError):
    default_error_code = "INVALID_FISCAL_DATA"

    def __init__(
        self,
        message: str = "La informacion fiscal registrada no es valida",
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )
