from typing import Any, Dict, Optional

from src.shared.errors.base_exception import NotFoundError


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
