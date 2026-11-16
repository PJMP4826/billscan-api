from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BaseAppException


class AuthenticationError(BaseAppException):
    """Credenciales ausentes o token no verificable.

    ``error_code`` tiene default para que los adapters puedan lanzarlo con solo
    el motivo técnico del SDK, sin exponerlo al cliente.
    """

    http_status = 401
    default_error_code = "AUTHENTICATION_ERROR"
    default_title = "Unauthorized"
    is_public = True

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
