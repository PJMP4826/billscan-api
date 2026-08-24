from abc import ABC, abstractmethod
from src.application.dtos.invoice_result_dto import InvoiceResult


class BillingWebhookHandlerPort(ABC):
    """
    Separate abstract port for webhook handling.

    Decoupled from BillingProviderPort intentionally:
    - Not all providers deliver results via webhooks.
    - Webhook verification logic is provider-specific (HMAC secret, header names).
    - Your FastAPI webhook endpoint depends on this port, not on the provider adapter.

    Providers that don't use webhooks should implement a no-op or raise
    NotImplementedError — the calling code decides whether to rely on
    webhooks or fall back to polling via get_invoice_status().
    """

    @abstractmethod
    def verify_signature(self, headers: dict[str, str], raw_body: bytes) -> bool:
        """
        Verify the webhook delivery is authentic.

        Returns True if the signature is valid, False otherwise.
        Never raises — signature failures are business logic, not exceptions.
        """
        ...

    @abstractmethod
    def parse_event(
        self, raw_body: dict[str, str | bool | dict[str, str]]
    ) -> InvoiceResult:
        """
        Parse the raw webhook payload into a domain InvoiceResult.

        Translates provider-specific event structure (factura.completed,
        factura.failed, or any future format) into the unified domain model.

        Raises:
            BillingWebhookParseError: if the payload cannot be parsed.
        """
        ...
