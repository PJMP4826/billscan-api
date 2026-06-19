from abc import ABC, abstractmethod
from src.domain.commands.invoice_request import InvoiceRequest
from src.domain.records.invoice_result import InvoiceResult
from src.domain.records.invoice_files import InvoiceFiles


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
    async def submit_invoice(self, request: InvoiceRequest) -> InvoiceResult:
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
    async def get_invoice_files(self, session_id: str) -> InvoiceFiles:
        """
        Retrieve the generated invoice files (XML + PDF download URLs).

        Should only be called after confirming status == COMPLETED.
        Raises BillingFilesNotReadyError if files are not yet available.

        Raises:
            BillingFilesNotReadyError: if session is still processing.
            BillingProviderError: on any other provider-level error.
        """
        raise NotImplementedError
