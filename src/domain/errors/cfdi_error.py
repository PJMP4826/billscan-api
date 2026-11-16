from typing import Any, Dict, Optional

from src.shared.errors.base_exception import NotFoundError


class CfdiNotFoundError(NotFoundError):
    default_error_code = "CFDI_NOT_FOUND"

    def __init__(
        self,
        message: str = "CFDI no encontrado",
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )
