from src.config.logger import logger

from src.domain.enums.job_names import JobName
from src.domain.enums.billing_status import BillingStatus
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.domain.ports.receipt_extractor import ReceiptExtractorPort

# repos
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort
from src.domain.ports.repositories.receipt_job_details_repository_port import (
    ReceiptJobDetailsRepositoryPort,
)
from src.domain.ports.repositories.receipt_billing_detail_repository_port import (
    ReceiptBillingDetailRepositoryPort,
)
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.ports.repositories.merchant_repository_port import (
    MerchantRepositoryPort,
)

from src.infrastructure.agents.ticket_extractor_agent.prompts.ticket_extractor_prompts import (
    TICKET_EXTRACTOR_AGENT,
)


class ProcessReceiptExtractionUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_repository: ReceiptRepositoryPort,
        receipt_job_details_repository: ReceiptJobDetailsRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
        merchant_repository: MerchantRepositoryPort,
        billing_detail_repository: ReceiptBillingDetailRepositoryPort,
        extractor: ReceiptExtractorPort,
        queue_publisher: QueuePublisherPort,
    ) -> None:
        self._file_storage = file_storage

        self._receipt_repository = receipt_repository
        self._receipt_job_details_repository = receipt_job_details_repository
        self._receipt_image_repository = receipt_image_repository
        self._merchant_repository = merchant_repository
        self._billing_detail_repository = billing_detail_repository

        self._extractor = extractor
        self._queue_publisher = queue_publisher

    async def execute(self, job_id: int, user_id: str, auto_billing: bool) -> None:
        try:
            await self._receipt_job_details_repository.mark_extracting(
                job_id=int(job_id)
            )

            images_records = await self._receipt_image_repository.find_by_job_id(
                receipt_job_id=int(job_id)
            )

            if not images_records:
                raise ValueError(f"No se encontraron imágenes para el job {job_id}")

            images_records.sort(key=lambda x: x.get("page_number", 1))

            image_pages_bytes: list[bytes] = []
            for record in images_records:
                img_bytes, _ = await self._file_storage.download(record["file_key"])
                image_pages_bytes.append(img_bytes)

            receipt = await self._extractor.extract(
                image_pages=image_pages_bytes,
                prompt_template_str=TICKET_EXTRACTOR_AGENT,
            )

            if not receipt:
                await self._receipt_job_details_repository.mark_failed(
                    job_id=int(job_id),
                    error_message="La extracción no devolvió resultado",
                )
                return

            merchant_id = await self._merchant_repository.find_or_create(
                merchant=receipt.merchant
            )
            receipt_id = await self._receipt_repository.save(
                receipt=receipt, merchant_id=merchant_id, user_id=user_id
            )

            await self._receipt_job_details_repository.mark_completed(
                job_id=int(job_id), receipt_id=receipt_id
            )

            await self._receipt_image_repository.backfill_receipt_id(
                receipt_id=receipt_id, receipt_job_id=job_id
            )

            if receipt.billing:
                if not receipt.billing.is_billable:
                    await self._billing_detail_repository.update_billing_status(
                        receipt_id=receipt_id, billing_status=BillingStatus.NOT_ELIGIBLE
                    )

                if receipt.billing.is_billable:
                    await self._billing_detail_repository.update_billing_status(
                        receipt_id=receipt_id, billing_status=BillingStatus.PENDING
                    )
                    if auto_billing is True:
                        self._queue_publisher.enqueue_job(
                            job_name=JobName.INITIATE_BILLING,
                            payload={"receipt_id": receipt_id, "user_id": user_id},
                        )

            logger.info(f"Receipt {receipt_id} extraído correctamente. ")

        except Exception as exc:
            logger.error(f"Fallo procesando receipt {job_id}: {exc}")
            await self._receipt_job_details_repository.mark_failed(
                job_id=int(job_id),
                error_message="La extracción no devolvió resultado",
            )
