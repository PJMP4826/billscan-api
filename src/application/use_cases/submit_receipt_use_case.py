import uuid

from src.config.logger import logger
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.tax_regime import TaxRegime
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)
from src.domain.ports.repositories.receipt_job_details_repository_port import (
    ReceiptJobDetailsRepositoryPort,
)
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.enums.job_names import JobName
from src.shared.errors.base_exception import BadRequestError


class SubmitReceiptUseCase:

    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_job_details_repository: ReceiptJobDetailsRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
        queue_publisher: QueuePublisherPort,
        fiscal_info_repository: FiscalInfoRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._receipt_job_details_repository = receipt_job_details_repository
        self._receipt_image_repository = receipt_image_repository
        self._queue_publisher = queue_publisher
        self._fiscal_info_repository = fiscal_info_repository

    async def execute(
        self,
        user_id: str,
        grouped_images: dict[str, list[dict[str, bytes | str]]],
        auto_billing: bool,
        uso_cfdi: InvoiceUse | None = None,
        regimen: TaxRegime | None = None,
    ) -> None:

        uso_cfdi_code = uso_cfdi.value if uso_cfdi is not None else None
        regimen_code = regimen.value if regimen is not None else None

        if regimen_code is not None:
            await self._ensure_regimen_belongs(
                user_id=user_id, regimen_code=regimen_code
            )

        # Iteramos sobre cada ticket (grupo)
        for group_key, file_details_list in grouped_images.items():
            logger.debug(f"Processing group: {group_key}")

            job_name = JobName.PROCESS_RECEIPT_EXTRACTION

            job_id = await self._receipt_job_details_repository.create(
                user_id=user_id, job_name=job_name
            )

            for page_idx, item in enumerate(file_details_list, start=1):

                file_data = item["file"]
                if not isinstance(file_data, bytes):
                    raise TypeError(
                        f"Se esperaba bytes, pero se recibió {type(file_data).__name__}"
                    )

                file_key = uuid.uuid4().hex
                mime_file_type = str(item["mime"])
                image_key = await self._file_storage.upload(
                    key=file_key,
                    data=file_data,
                    mime_type=mime_file_type,
                )

                await self._receipt_image_repository.insert(
                    receipt_job_id=job_id,
                    file_key=image_key,
                    mime_type=mime_file_type,
                    page_number=page_idx,
                )

            self._queue_publisher.enqueue_job(
                job_name=job_name,
                payload={
                    "job_id": job_id,
                    "user_id": user_id,
                    "auto_billing": auto_billing,
                    "uso_cfdi": uso_cfdi_code,
                    "regimen": regimen_code,
                },
            )

    async def _ensure_regimen_belongs(self, user_id: str, regimen_code: str) -> None:
        """Valida que el régimen elegido pertenezca a los registrados del RFC."""
        regimens = await self._fiscal_info_repository.get_regimens_by_user_id(
            user_id=user_id
        )
        registered_codes = {item["code"] for item in regimens}

        if not registered_codes:
            raise BadRequestError(
                "No hay regímenes fiscales registrados para el usuario; "
                "registra tu informacion fiscal antes de facturar"
            )

        if regimen_code not in registered_codes:
            raise BadRequestError(
                f"El régimen fiscal {regimen_code} no está asociado al RFC del usuario"
            )
