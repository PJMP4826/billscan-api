from typing import Any, Dict, Optional

from src.shared.errors.base_exception import ConflictError


class InvoiceQuotaExceededError(ConflictError):
    """El RFC ya consumió todas las facturas permitidas."""

    default_error_code = "INVOICE_QUOTA_EXCEEDED"

    def __init__(
        self,
        limit: int,
        used: int,
        message: Optional[str] = None,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message
            or (
                f"Alcanzaste el límite de {limit} facturas permitidas para tu RFC "
                f"({used} de {limit} usadas)."
            ),
            error_code=error_code,
            details=details or {"limit": limit, "used": used},
            **kwargs,
        )
