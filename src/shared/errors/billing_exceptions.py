class BillingProviderError(Exception):
    """
    Base exception for all billing provider errors.
    Carries the provider's own error code for logging/debugging.
    """

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


class BillingAuthError(BillingProviderError):
    """API key is missing, invalid, or revoked."""


class BillingInsufficientBalanceError(BillingProviderError):
    """Account does not have enough credits."""


class BillingFilesNotReadyError(BillingProviderError):
    """Files requested before the invoice reached COMPLETED status."""


class BillingSessionNotFoundError(BillingProviderError):
    """The session_id does not exist or belongs to another account."""


class BillingExternalIdConflictError(BillingProviderError):
    """Same external_id was sent with a different payload."""


class BillingUnreadableTicketError(BillingProviderError):
    """OCR could not extract data from the ticket image."""


class BillingRateLimitError(BillingProviderError):
    """Too many requests — caller should implement backoff."""


class BillingWebhookParseError(Exception):
    """Webhook payload could not be parsed into a domain model."""


class BillingWebhookSignatureError(Exception):
    """Webhook signature verification failed."""
