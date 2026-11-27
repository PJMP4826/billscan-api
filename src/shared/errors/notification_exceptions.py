from typing import Any, Dict, Optional

from src.shared.errors.infrastructure_exceptions import InfrastructureException


class NotificationProviderError(InfrastructureException):
    """Error base del proveedor de notificaciones (Expo).

    Los fallos de una petición completa se lanzan; los fallos por
    destinatario (``DeviceNotRegistered``, ``MessageTooBig``, ...) se
    devuelven en los DTOs, no se lanzan.
    """

    http_status = 502
    default_error_code = "NOTIFICATION_PROVIDER_ERROR"
    default_title = "Bad Gateway"
    is_public = False


class NotificationAuthError(NotificationProviderError):
    """Credenciales inválidas o ausentes del proveedor."""

    http_status = 401
    default_error_code = "NOTIFICATION_AUTH_ERROR"
    default_title = "Unauthorized"


class NotificationBadRequestError(NotificationProviderError):
    """La petición es inválida (payload malformado, límites excedidos)."""

    http_status = 400
    default_error_code = "NOTIFICATION_BAD_REQUEST"
    default_title = "Bad Request"


class NotificationRateLimitError(NotificationProviderError):
    """Se superó el límite de peticiones del proveedor. Reintentable."""

    http_status = 429
    default_error_code = "NOTIFICATION_RATE_LIMIT"
    default_title = "Too Many Requests"

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[float] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            retryable=True,
            **kwargs,
        )


class NotificationServerError(NotificationProviderError):
    """El proveedor falló con 5xx. Reintentable."""

    http_status = 502
    default_error_code = "NOTIFICATION_SERVER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            retryable=True,
            **kwargs,
        )


class NotificationTransportError(NotificationProviderError):
    """La petición HTTP no se completó (DNS, conexión, TLS, ...). Reintentable."""

    default_error_code = "NOTIFICATION_TRANSPORT_ERROR"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            error_code=error_code,
            details=details,
            retryable=True,
            **kwargs,
        )


class NotificationTimeoutError(NotificationTransportError):
    """La petición al proveedor excedió el timeout. Reintentable."""

    default_error_code = "NOTIFICATION_TIMEOUT"

    def __init__(
        self,
        message: str = "La petición al proveedor de notificaciones excedió el timeout",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)


class NotificationUnexpectedResponseError(NotificationProviderError):
    """El proveedor respondió 200 pero con una forma inesperada."""

    default_error_code = "NOTIFICATION_UNEXPECTED_RESPONSE"
