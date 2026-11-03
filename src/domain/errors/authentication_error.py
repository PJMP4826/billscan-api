from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BaseAppException


class AuthenticationError(BaseAppException):
    """Credenciales ausentes o token no verificable.

    `error_code` tiene default para que los adapters puedan lanzarlo con solo
    el motivo técnico del SDK, sin exponerlo al cliente.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details or {})
