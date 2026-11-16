from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BaseAppException


class BillingProviderError(BaseAppException):
    """
    Base exception for all billing provider errors.
    Carries the provider's own error code for logging/debugging.
    """

    http_status = 502
    default_error_code = "BILLING_PROVIDER_ERROR"
    default_title = "Bad Gateway"
    is_public = False

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )


class BillingAuthError(BillingProviderError):
    """API key is missing, invalid, or revoked."""

    default_error_code = "BILLING_AUTH_ERROR"


class BillingInsufficientBalanceError(BillingProviderError):
    """Account does not have enough credits."""

    http_status = 402
    default_error_code = "BILLING_INSUFFICIENT_BALANCE"
    default_title = "Payment Required"


class BillingFilesNotReadyError(BillingProviderError):
    """Files requested before the invoice reached COMPLETED status."""

    http_status = 409
    default_error_code = "BILLING_FILES_NOT_READY"
    default_title = "Conflict"


class BillingSessionNotFoundError(BillingProviderError):
    """The session_id does not exist or belongs to another account."""

    http_status = 404
    default_error_code = "BILLING_SESSION_NOT_FOUND"
    default_title = "Not Found"


class BillingExternalIdConflictError(BillingProviderError):
    """Same external_id was sent with a different payload."""

    http_status = 409
    default_error_code = "BILLING_EXTERNAL_ID_CONFLICT"
    default_title = "Conflict"


class BillingUnreadableTicketError(BillingProviderError):
    """OCR could not extract data from the ticket image."""

    http_status = 422
    default_error_code = "BILLING_UNREADABLE_TICKET"
    default_title = "Unprocessable Entity"


class BillingRateLimitError(BillingProviderError):
    """Too many requests — caller should implement backoff."""

    http_status = 429
    default_error_code = "BILLING_RATE_LIMIT"
    default_title = "Too Many Requests"


class BillingWebhookParseError(BaseAppException):
    """Webhook payload could not be parsed into a domain model."""

    http_status = 400
    default_error_code = "WEBHOOK_PARSE_ERROR"
    default_title = "Bad Request"
    is_public = True


class BillingWebhookSignatureError(BaseAppException):
    """Webhook signature verification failed."""

    http_status = 401
    default_error_code = "WEBHOOK_SIGNATURE_INVALID"
    default_title = "Unauthorized"
    is_public = True
