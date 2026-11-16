from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BadRequestError


class RegimenNotRegisteredError(BadRequestError):
    default_error_code = "REGIMEN_NOT_REGISTERED"

    def __init__(
        self,
        regimen_code: str,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message
            or (
                f"El régimen fiscal {regimen_code} no está asociado "
                "al RFC del usuario"
            ),
            error_code=error_code,
            details={"regimen": regimen_code, **(details or {})},
            **kwargs,
        )


class NoRegisteredRegimensError(BadRequestError):
    default_error_code = "NO_REGISTERED_REGIMENS"

    def __init__(
        self,
        message: str = (
            "No hay regímenes fiscales registrados para el usuario; "
            "registra tu informacion fiscal antes de facturar"
        ),
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )
