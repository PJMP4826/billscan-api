"""
FacturaGPT concrete implementation of BillingProviderPort.

Responsibilities:
- Translate InvoiceRequestCommand (domain) → FacturaGPT request body (dict)
- Call FacturaGPT API via httpx with proper auth headers
- Deserialize response using Pydantic schemas (type-safe, not raw dicts)
- Translate FacturaGPT response schemas → InvoiceResult (domain)
- Map FacturaGPT HTTP/error codes → port-level exceptions

Nothing above this file knows about FacturaGPT. Nothing below knows about
domain models. This file is the only translation boundary.
"""

import httpx
from src.config.logger import logger

from src.application.commands.invoice_request_command import InvoiceRequestCommand
from src.application.dtos.invoice_result_dto import InvoiceResult
from src.application.dtos.invoice_files_dto import InvoiceFiles
from src.application.dtos.ocr_result_dto import OcrResult

from src.domain.enums.billing_status import BillingStatus

from src.domain.ports.billing_provider import BillingProviderPort
from src.shared.errors.billing_exceptions import (
    BillingAuthError,
    BillingExternalIdConflictError,
    BillingFilesNotReadyError,
    BillingInsufficientBalanceError,
    BillingProviderError,
    BillingRateLimitError,
    BillingSessionNotFoundError,
    BillingUnreadableTicketError,
)
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_files_response import (
    FacturaGPTFilesResponse,
)
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_status_response import (
    FacturaGPTStatusResponse,
)
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_submit_response import (
    FacturaGPTSubmitResponse,
)
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_error import (
    FacturaGPTError,
)
from src.infrastructure.schemas.factura_gpt_schemas.facturagpt_ocr_result import (
    FacturaGPTOcrResult,
)

_ERROR_CODE_MAP: dict[str, type[BillingProviderError]] = {
    "INVALID_API_KEY": BillingAuthError,
    "EXPIRED_API_KEY": BillingAuthError,
    "INSUFFICIENT_BALANCE": BillingInsufficientBalanceError,
    "SESSION_NOT_FOUND": BillingSessionNotFoundError,
    "EXTERNAL_ID_CONFLICT": BillingExternalIdConflictError,
    "UNREADABLE_TICKET": BillingUnreadableTicketError,
    "RFC_NOT_FOUND": BillingUnreadableTicketError,
    "FILES_NOT_AVAILABLE": BillingFilesNotReadyError,
    "RATE_LIMIT_EXCEEDED": BillingRateLimitError,
}

# Nota FacturaGPTError, FacturaGPTMeta, CfdiSummary no se esta mapeando a nada


class FacturaGPTBillingAdapter(BillingProviderPort):
    """
    Concrete FacturaGPT implementation of BillingProviderPort.

    Pass an httpx.AsyncClient from the outside (dependency injection)
    so the client's lifecycle (connection pooling, timeouts, retries)
    is controlled by the caller — not buried inside this class.
    """

    BASE_URL = "https://api.facturagpt.com.mx"

    def __init__(self, base_url: str, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None
        self._base_url = base_url if base_url else self.BASE_URL

    # ------------------------------------------------------------------
    # BillingProviderPort implementation
    # ------------------------------------------------------------------

    async def submit_invoice(self, request: InvoiceRequestCommand) -> InvoiceResult:
        body = self._build_submit_body(request)
        raw = await self._post("/api/v1/get_factura", body)

        if "detail" in raw:
            raise BillingProviderError(f"API Error: {raw['detail']}")

        parsed = FacturaGPTSubmitResponse.model_validate(raw)
        # self._raise_if_error(parsed.ok, parsed.error)

        result = InvoiceResult()

        if parsed.error:
            status = parsed.error.details.get("status", "processing")  # type: ignore
            result = InvoiceResult(
                session_id=parsed.meta.session_id,
                error_code=parsed.error.code,
                error_message=parsed.error.message,
                status=BillingStatus(status.upper()),
            )

        data = parsed.data
        if data:
            result = InvoiceResult(
                session_id=data.session_id,
                external_id=data.external_id,
                status=BillingStatus(data.status.upper()),
                ocr_result=self._map_ocr(data.ocr_result),
            )

        return result

    async def get_invoice_status(self, session_id: str) -> InvoiceResult:
        raw = await self._get(f"/api/v1/get_factura_status/{session_id}")
        parsed = FacturaGPTStatusResponse.model_validate(raw)
        # self._raise_if_error(parsed.ok, parsed.error)

        result = InvoiceResult()

        if parsed.error:
            status = parsed.error.details.get("status", "processing")  # type: ignore
            result = InvoiceResult(
                session_id=parsed.meta.session_id,
                error_code=parsed.error.code,
                status=BillingStatus(status.upper()),
            )

        data = parsed.data
        if data:
            result = InvoiceResult(
                session_id=data.session_id, status=BillingStatus(data.status.upper())
            )

        return result

    async def get_invoice_files(self, session_id: str) -> InvoiceResult | InvoiceFiles:
        raw = await self._get(f"/api/v1/get_factura_files/{session_id}")
        parsed = FacturaGPTFilesResponse.model_validate(raw)
        # self._raise_if_error(parsed.ok, parsed.error)

        result = InvoiceResult()

        if parsed.error:
            status = parsed.error.details.get("status", "processing")  # type: ignore
            result = InvoiceResult(
                session_id=parsed.meta.session_id,
                error_code=parsed.error.code,
                status=BillingStatus(status.upper()),
            )

        data = parsed.data
        if data:
            result = InvoiceFiles(
                xml_url=data.xml_url,
                pdf_url=data.pdf_url,
            )
        return result

    async def download_invoice_file(self, url: str) -> tuple[bytes, str]:
        """
        Descarga los bytes crudos de un archivo de factura (XML/PDF) usando
        la URL de descarga incluida en el webhook (download proxy de
        FacturaGPT). Se autentica con la misma API key del partner y sigue
        los redirects firmados del proxy.

        Returns:
            tuple[bytes, str]: (bytes del archivo, content-type).
        """
        if self._client is None:
            raise RuntimeError(
                "HTTPX client not initialized. Call .startup() on FacturaGPTBillingAdapter first."
            )

        try:
            response = await self._client.get(
                url,
                headers=self._auth_headers,
                follow_redirects=True,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(
                "No se pudo descargar el archivo de factura desde %s: %s",
                url,
                e,
                exc_info=True,
            )
            raise BillingProviderError(
                f"No se pudo descargar el archivo de factura: {url}",
                error_code="INVOICE_FILE_DOWNLOAD_ERROR",
            ) from e

        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return response.content, content_type

    async def startup(self) -> None:
        """
        Initializes the httpx.AsyncClient.
        This method should be called once during application startup.
        """
        if self._client is None:
            self._client = httpx.AsyncClient()
            logger.info("FacturaGPTBillingAdapter: httpx.AsyncClient initialized.")
        else:
            logger.warning(
                "FacturaGPTBillingAdapter: httpx.AsyncClient already initialized."
            )
            return

    async def shutdown(self) -> None:
        """
        Closes the httpx.AsyncClient.
        This method should be called once during application shutdown.
        """
        if self._client:
            await self._client.aclose()
            self._client = None  # Clear the client after closing
            logger.info("FacturaGPTBillingAdapter: httpx.AsyncClient closed.")
        else:
            logger.warning(
                "FacturaGPTBillingAdapter: httpx.AsyncClient not initialized or already closed."
            )  # Si tienes un logger
            return

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _post(
        self, path: str, body: dict[str, str | bool | dict[str, str]]
    ) -> dict[str, str | bool | dict[str, str] | None]:
        if self._client is None:
            raise RuntimeError(
                "HTTPX client not initialized. Call .startup() on FacturaGPTBillingAdapter first."
            )
        response = await self._client.post(
            f"{self._base_url}{path}",
            json=body,
            headers=self._auth_headers,
        )
        return response.json()

    async def _get(self, path: str) -> dict[str, str | bool | dict[str, str] | None]:
        if self._client is None:
            raise RuntimeError(
                "HTTPX client not initialized. Call .startup() on FacturaGPTBillingAdapter first."
            )
        response = await self._client.get(
            f"{self._base_url}{path}",
            headers=self._auth_headers,
        )
        return response.json()

    def _raise_if_error(self, ok: bool, error: FacturaGPTError | None) -> None:
        """
        Translate FacturaGPT error codes into port-level exceptions.
        Never lets provider-specific error structures leak to callers.
        """
        if ok:
            return
        if error is None:
            raise BillingProviderError("Unknown provider error", error_code=None)

        exc_class = _ERROR_CODE_MAP.get(error.code, BillingProviderError)
        raise exc_class(error.message, error_code=error.code)

    def _build_submit_body(
        self, request: InvoiceRequestCommand
    ) -> dict[str, str | bool | dict[str, str]]:
        """
        Translate domain InvoiceRequestCommand → FacturaGPT-specific request dict.
        This is the only place FacturaGPT field names appear on the input side.
        """
        body: dict[str, str | bool | dict[str, str]] = {
            "external_id": request.external_id,
            "ticket_image": request.ticket_image_b64,
            "uso_cfdi": request.invoice_use.value,
            "payment_method": request.payment_method.value,  # type: ignore
            "save_customer": request.save_customer,
            "test_mode": request.test_mode,
        }

        if request.webhook_url:
            body["webhook_url"] = request.webhook_url

        if request.customer_id:
            body["customer_id"] = request.customer_id
        elif request.customer_info:
            info = request.customer_info
            body["user_info"] = {
                "razon_social": info.razon_social,
                "rfc": info.rfc,
                "email": info.email,
                "regimen": info.regimen.value,
                "cp": info.cp,
                **({"address": info.address} if info.address else {}),
            }

        return body

    @staticmethod
    def _map_ocr(ocr: FacturaGPTOcrResult | None) -> OcrResult | None:
        if ocr is None:
            return None
        return OcrResult(
            merchant_name=ocr.merchant_name,
            merchant_rfc=ocr.merchant_rfc,
            amount=ocr.amount,
            net_amount=ocr.net_amount,
            tax_amount=ocr.tax_amount,
            tax_rate=ocr.tax_rate,
            currency=ocr.currency,
            date=ocr.date,
            payment_method=ocr.payment_method,
            ticket_readable=ocr.ticket_readable,
        )
