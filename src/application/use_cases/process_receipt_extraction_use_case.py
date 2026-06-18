from src.config.logger import logger

import httpx

from src.domain.entities.receipt import Receipt
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.domain.ports.receipt_extractor import ReceiptExtractorPort

# repos
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort
from src.domain.ports.repositories.receipt_job_details_repository_port import (
    ReceiptJobDetailsRepositoryPort,
)
from src.domain.ports.repositories.receipt_item_repository_port import (
    ReceiptItemRepositoryPort,
)
from src.domain.ports.repositories.receipt_tax_repository_port import (
    ReceiptTaxRepositoryPort,
)
from src.domain.ports.repositories.receipt_payment_repository_port import (
    ReceiptPaymentRepositoryPort,
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
        item_repository: ReceiptItemRepositoryPort,
        tax_repository: ReceiptTaxRepositoryPort,
        payment_repository: ReceiptPaymentRepositoryPort,
        billing_detail_repository: ReceiptBillingDetailRepositoryPort,
        extractor: ReceiptExtractorPort,
        queue_publisher: QueuePublisherPort,
    ) -> None:
        self._file_storage = file_storage

        self._receipt_repository = receipt_repository
        self._receipt_job_details_repository = receipt_job_details_repository
        self._receipt_image_repository = receipt_image_repository
        self._merchant_repository = merchant_repository
        self._item_repository = item_repository
        self._tax_repository = tax_repository
        self._payment_repository = payment_repository
        self._billing_detail_repository = billing_detail_repository

        self._extractor = extractor
        self._queue_publisher = queue_publisher

    async def execute(self, job_id: int, user_id: str) -> None:
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
                img_bytes = await self._get_file_as_bytes_async(record["file_url"])
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
            receipt_id = await self._receipt_repository.insert(
                receipt=receipt, merchant_id=merchant_id, user_id=user_id
            )

            await self._persist_receipt_relations(
                receipt_id=receipt_id, receipt=receipt
            )

            await self._receipt_job_details_repository.mark_completed(
                job_id=int(job_id), receipt_id=receipt_id
            )

            await self._receipt_image_repository.backfill_receipt_id(
                receipt_id=receipt_id, receipt_job_id=job_id
            )

            if receipt.billing and receipt.billing.is_billable:
                self._queue_publisher.enqueue_job(
                    job_name="INITIATE_BILLING",
                    payload={"receipt_id": receipt_id},
                )
                logger.info(
                    "Flujo de facturación pendiente de implementar (fuera de alcance)."
                )

            logger.info(f"Receipt {receipt_id} extraído correctamente. ")

        except Exception as exc:
            logger.error(f"Fallo procesando receipt {job_id}: {exc}")
            await self._receipt_job_details_repository.mark_failed(
                job_id=int(job_id),
                error_message="La extracción no devolvió resultado",
            )

    async def _persist_receipt_relations(
        self, receipt_id: int, receipt: Receipt
    ) -> None:
        """
        logica de insercion de todas las entidades relacionadas a un Receipt
        """
        # Items
        if receipt.items:
            await self._item_repository.insert_many(receipt_id, receipt.items)

        # Taxes
        if receipt.totals and receipt.totals.taxes:
            await self._tax_repository.insert_many(receipt_id, receipt.totals.taxes)

        # Payments
        if receipt.payment:
            await self._payment_repository.insert(
                receipt_id=receipt_id,
                payment_method_code=receipt.payment.method_code.value,  # type: ignore
                amount=receipt.totals.amount_paid,
                card_last_four=receipt.payment.card_last_four,
                authorization_code=receipt.payment.authorization_code,
            )

        # Billing Details (1:1)
        await self._billing_detail_repository.insert(
            receipt_id=receipt_id, billing=receipt.billing
        )

    async def _get_file_as_bytes_async(self, url: str) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.content
