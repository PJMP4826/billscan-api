from typing import Any, Dict, Optional

from src.shared.errors.base_exception import ConflictError


def _invoice_phrase(count: int, quota_label: str) -> str:
    noun = "factura" if count == 1 else "facturas"
    return f"{noun} {quota_label}"


def _availability_phrase(remaining: int, quota_label: str) -> str:
    if remaining == 1:
        return f"solo te queda 1 {_invoice_phrase(1, quota_label)}"
    return f"solo te quedan {remaining} {_invoice_phrase(remaining, quota_label)}"


def build_quota_message(
    limit: int,
    used: int,
    requested: int,
    remaining: int,
    quota_label: str = "gratis",
) -> str:
    requested_count = f"{requested} {_invoice_phrase(requested, quota_label)}"

    if limit <= 0:
        return f"Este RFC no tiene {_invoice_phrase(2, quota_label)} disponibles."

    if remaining <= 0:
        return (
            f"Ya usaste {used} de {limit} "
            f"{_invoice_phrase(limit, quota_label)} de este RFC; "
            f"tu solicitud de {requested_count} no se procesó."
        )

    if used == 0:
        return (
            f"El máximo es {limit} {_invoice_phrase(limit, quota_label)} por RFC "
            f"y solicitaste {requested}. Reduce el lote a {limit}."
        )

    return (
        f"Tu solicitud de {requested_count} excede el límite: "
        f"{_availability_phrase(remaining, quota_label)} en este RFC "
        f"({used} de {limit} usadas). Reduce el lote a {remaining}."
    )


class InvoiceQuotaExceededError(ConflictError):
    """El RFC ya consumió todas las facturas permitidas."""

    default_error_code = "INVOICE_QUOTA_EXCEEDED"

    def __init__(
        self,
        limit: int,
        used: int,
        message: Optional[str] = None,
        *,
        requested: int = 1,
        quota_label: str = "gratis",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        remaining = max(limit - used, 0)
        super().__init__(
            message
            or build_quota_message(
                limit, used, requested, remaining, quota_label
            ),
            error_code=error_code,
            details=details or {
                "limit": limit,
                "used": used,
                "requested": requested,
                "remaining": remaining,
                "quota_label": quota_label,
            },
            **kwargs,
        )
