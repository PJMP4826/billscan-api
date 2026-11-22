import asyncio
import base64

from src.config.logger import logger
from src.config.settings import settings
from src.domain.enums.billing_status import BillingStatus
from src.domain.enums.job_names import JobName
from src.shared.errors.infrastructure_exceptions import InfrastructureException
from src.domain.value_objects.billing_failure import BillingFailure
from src.domain.errors.billing_error import (
    InvoiceQuotaExceededError,
    build_quota_message,
)
from src.domain.ports.billing_provider import BillingProviderPort
from src.domain.enums.tax_regime import TaxRegime
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.sat_payment_methods import SatPaymentMethodCode
from src.application.commands.invoice_request_command import InvoiceRequestCommand
from src.domain.ports.file_storage_port import FileStoragePort
from src.application.dtos.billing_customer_dto import BillingCustomerInfoDto
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.domain.ports.repositories.receipt_billing_detail_repository_port import (
    ReceiptBillingDetailRepositoryPort,
)
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort
from src.domain.ports.repositories.invoice_quota_repository_port import (
    InvoiceQuotaRepositoryPort,
)
from src.domain.ports.rfc_fingerprint_port import RfcFingerprintPort
from src.domain.ports.data_encryptor import DataEncryptor
from src.domain.ports.queue_publisher_port import QueuePublisherPort


class InitiateBillingUseCase:
    def __init__(
        self,
        billing_provider: BillingProviderPort,
        billing_detail_repository: ReceiptBillingDetailRepositoryPort,
        fiscal_info_repository_port: FiscalInfoRepositoryPort,
        receipt_image_repository_port: ReceiptImageRepositoryPort,
        receipt_repository: ReceiptRepositoryPort,
        encryptor: DataEncryptor,
        file_storage: FileStoragePort,
        invoice_quota_repository: InvoiceQuotaRepositoryPort,
        rfc_fingerprint: RfcFingerprintPort,
        max_invoices_per_rfc: int,
        queue_publisher: QueuePublisherPort | None = None,
        max_storage_retries: int = 3,
        storage_retry_delay_seconds: float = 5.0,
    ) -> None:
        self._billing_provider = billing_provider
        self._billing_detail_repository = billing_detail_repository
        self._fiscal_info_repository = fiscal_info_repository_port
        self._receipt_image_repository = receipt_image_repository_port
        self._receipt_repository = receipt_repository
        self._encryptor = encryptor
        self._file_storage = file_storage
        self._invoice_quota_repository = invoice_quota_repository
        self._rfc_fingerprint = rfc_fingerprint
        self._max_invoices_per_rfc = max_invoices_per_rfc
        self._queue_publisher = queue_publisher
        self._max_storage_retries = max(0, max_storage_retries)
        self._storage_retry_delay_seconds = max(0.0, storage_retry_delay_seconds)

    async def execute(self, payload: dict[str, str | int]) -> None:
        receipt_id = int(payload["receipt_id"])
        user_id = str(payload["user_id"])
        storage_retry_count = int(payload.get("storage_retry_count") or 0)

        response = None
        try:
            # Obtener las imagenes del ticket necesarias para la factura

            # Esta es una list de images, por ahora no se uniran las imagenes (un ticket puede tener varias fotos)
            # solo se contemplara una unica imagen por ticket (image[0])
            image = await self._receipt_image_repository.find_by_receipt_id(
                receipt_id=receipt_id
            )

            image = image[0]

            img_bytes, _ = await self._file_storage.download(image["file_key"])

            image_base64 = base64.b64encode(img_bytes).decode("utf-8")

            fiscal_user_info = await self._fiscal_info_repository.get_latest_by_user_id(
                user_id=user_id
            )

            # El uso de CFDI y el régimen los elige el cliente en la request del
            # ticket y quedan persistidos en `receipt_billing_details`. Si no los
            # envió, caemos a los valores por defecto de `fiscal_info` para
            # mantener compatibilidad con clientes viejos.
            billing_detail = await self._billing_detail_repository.find_by_receipt_id(
                receipt_id=receipt_id
            )

            persisted_uso_cfdi = (
                billing_detail.get("uso_cfdi") if billing_detail else None
            )
            persisted_regimen = (
                billing_detail.get("regimen_code") if billing_detail else None
            )

            effective_uso_cfdi = (
                persisted_uso_cfdi or fiscal_user_info["use_cfdi_default"]
            )
            effective_regimen = persisted_regimen or fiscal_user_info["regimen_code"]

            await self._billing_detail_repository.set_billing_preferences(
                receipt_id=receipt_id,
                uso_cfdi=effective_uso_cfdi,
                regimen_code=effective_regimen,
            )

            rfc = self._encryptor.decrypt(fiscal_user_info["rfc"])
            rfc_hash = self._rfc_fingerprint.fingerprint(rfc)

            if not await self._invoice_quota_repository.try_reserve(
                receipt_id=receipt_id,
                rfc_hash=rfc_hash,
                max_invoices=self._max_invoices_per_rfc,
            ):
                logger.info(
                    "Receipt %s bloqueado: RFC alcanzó el límite de %s facturas",
                    receipt_id,
                    self._max_invoices_per_rfc,
                )
                used = await self._invoice_quota_repository.count_in_use(
                    rfc_hash=rfc_hash
                )
                remaining = max(self._max_invoices_per_rfc - used, 0)
                await self._billing_detail_repository.update_billing_status(
                    receipt_id=receipt_id,
                    billing_status=BillingStatus.QUOTA_EXCEEDED,
                    billing_error_code=InvoiceQuotaExceededError.default_error_code,
                    billing_error_message=build_quota_message(
                        limit=self._max_invoices_per_rfc,
                        used=used,
                        requested=1,
                        remaining=remaining,
                    ),
                )
                return

            user_info = BillingCustomerInfoDto(
                razon_social=self._encryptor.decrypt(fiscal_user_info["razon_social"]),
                rfc=rfc,
                email=self._encryptor.decrypt(fiscal_user_info["fiscal_email"]),
                regimen=TaxRegime(effective_regimen),
                cp=self._encryptor.decrypt(fiscal_user_info["cp"]),
                address=self._encryptor.decrypt(fiscal_user_info["address"]),
            )

            receipt = await self._receipt_repository.find_by_id(receipt_id=receipt_id)

            request = InvoiceRequestCommand(
                ticket_image_b64=image_base64,
                external_id=receipt.receipt_uuid,
                payment_method=SatPaymentMethodCode(
                    (
                        receipt.payment.method_code.value
                        if receipt.payment.method_code
                        else None
                    )
                ),
                invoice_use=InvoiceUse(effective_uso_cfdi),
                customer_info=user_info,
                test_mode=settings.facturagpt_test_mode,
            )

            logger.info(f"Iniciando timbrado externo para el receipt {receipt_id}...")

            response = await self._billing_provider.submit_invoice(request=request)

            # 4. Actualizar con el Session ID externo que te da FacturaGPT
            await self._billing_detail_repository.update_billing_status(
                receipt_id=receipt_id,
                billing_status=BillingStatus.PROCESSING,
                facturagpt_session_id=response.session_id,
                billing_error_code=response.error_code,
                billing_error_message=response.error_message,
            )

            logger.info(f"Receipt {receipt_id} enviado a servicio de facturacion")
        except Exception as exc:
            if self._should_retry_storage_error(exc, storage_retry_count):
                await self._schedule_storage_retry(
                    receipt_id=receipt_id,
                    user_id=user_id,
                    exc=exc,
                    storage_retry_count=storage_retry_count,
                    response=response,
                )
                return

            logger.error(
                f"Error al iniciar facturación para el receipt {receipt_id}: {exc}"
            )

            failure = BillingFailure.from_exception(exc)

            # Solo devolvemos el cupo si el proveedor NO aceptó la factura.
            # Si ya devolvió un session_id, la factura sigue en curso y debe
            # conservar su lugar en la cuota.
            if response is None:
                await self._release_quota(receipt_id)

            await self._billing_detail_repository.update_billing_status(
                receipt_id=receipt_id,
                billing_status=BillingStatus.FAILED,
                billing_error_code=failure.code,
                billing_error_message=failure.message,
            )

    def _should_retry_storage_error(
        self, exc: Exception, storage_retry_count: int
    ) -> bool:
        return (
            self._queue_publisher is not None
            and isinstance(exc, InfrastructureException)
            and exc.retryable
            and storage_retry_count < self._max_storage_retries
        )

    async def _schedule_storage_retry(
        self,
        *,
        receipt_id: int,
        user_id: str,
        exc: InfrastructureException,
        storage_retry_count: int,
        response: object | None,
    ) -> None:
        attempt = storage_retry_count + 1
        logger.warning(
            "Fallo transitorio de almacenamiento para el receipt %s (%s). "
            "Reintento %d/%d en %.1fs",
            receipt_id,
            exc.error_code,
            attempt,
            self._max_storage_retries,
            self._storage_retry_delay_seconds,
        )

        if response is None:
            await self._release_quota(receipt_id)

        await self._billing_detail_repository.update_billing_status(
            receipt_id=receipt_id,
            billing_status=BillingStatus.PENDING,
            billing_error_code=exc.error_code,
            billing_error_message=(
                "Fallo temporal de almacenamiento; "
                f"reintento {attempt}/{self._max_storage_retries}"
            ),
        )

        payload = {
            "receipt_id": receipt_id,
            "user_id": user_id,
            "storage_retry_count": attempt,
        }

        if self._storage_retry_delay_seconds <= 0:
            self._queue_publisher.enqueue_job(  # type: ignore[union-attr]
                job_name=JobName.INITIATE_BILLING,
                payload=payload,
            )
            return

        loop = asyncio.get_running_loop()
        loop.call_later(
            self._storage_retry_delay_seconds,
            self._queue_publisher.enqueue_job,  # type: ignore[union-attr]
            JobName.INITIATE_BILLING,
            payload,
        )

    async def _release_quota(self, receipt_id: int) -> None:
        try:
            await self._invoice_quota_repository.release(receipt_id)
        except Exception as release_exc:
            logger.error(
                "No se pudo liberar la cuota del receipt %s: %s",
                receipt_id,
                release_exc,
            )
