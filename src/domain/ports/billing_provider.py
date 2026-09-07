from abc import ABC, abstractmethod
from src.application.commands.invoice_request_command import InvoiceRequestCommand
from src.application.dtos.invoice_result_dto import InvoiceResult
from src.application.dtos.invoice_files_dto import InvoiceFiles


class BillingProviderPort(ABC):
    """
    Abstract billing provider port.

    Any class that implements this port can be swapped in as the billing
    backend without changes to the calling code.

    Implementors:
    - FacturaGPTAdapter
    - (future) OwnBillingAdapter
    - (future) AnyOtherProviderAdapter
    """

    @abstractmethod
    async def submit_invoice(self, request: InvoiceRequestCommand) -> InvoiceResult:
        """
        Submit a receipt image and customer info to start invoice generation.

        Returns an InvoiceResult with status=PROCESSING immediately.
        The final result arrives asynchronously — either via webhook or
        by polling get_invoice_status().

        Raises:
            BillingProviderError: on any provider-level error.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_invoice_status(self, session_id: str) -> InvoiceResult:
        """
        Poll the current status of a previously submitted invoice.

        Use this for reconciliation or as the primary result mechanism
        when the provider does not support webhooks.

        Raises:
            BillingProviderError: if session_id is not found or request fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_invoice_files(self, session_id: str) -> InvoiceResult | InvoiceFiles:
        """
        Retrieve the generated invoice files (XML + PDF download URLs).

        Should only be called after confirming status == COMPLETED.
        Raises BillingFilesNotReadyError if files are not yet available.

        Raises:
            BillingFilesNotReadyError: if session is still processing.
            BillingProviderError: on any other provider-level error.
        """
        raise NotImplementedError

    @abstractmethod
    async def download_invoice_file(self, url: str) -> tuple[bytes, str]:
        """
        Download the raw bytes of an invoice file (XML or PDF) using the
        download URL included in a webhook delivery (e.g.
        https://api.facturagpt.com.mx/api/v1/files/{session_id}/xml).

        Providers that cannot download files should raise
        NotImplementedError — callers decide whether the flow depends on it.

        Returns:
            tuple[bytes, str]: (raw file bytes, content-type header value).

        Raises:
            BillingProviderError: on any provider-level error.
        """
        raise NotImplementedError
