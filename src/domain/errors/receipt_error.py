from typing import Any, Dict, Optional

from src.shared.errors.base_exception import NotFoundError


class ReceiptNotFoundError(NotFoundError):
    default_error_code = "RECEIPT_NOT_FOUND"

    def __init__(
        self,
        message: str = "Ticket no encontrado",
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )


class ReceiptImageNotFoundError(NotFoundError):
    default_error_code = "RECEIPT_IMAGE_NOT_FOUND"

    def __init__(
        self,
        message: str = "Imagen no encontrada",
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )
