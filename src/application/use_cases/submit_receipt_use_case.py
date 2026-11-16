import uuid
from typing import Any

from src.config.logger import logger
from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.person_type import PersonType
from src.domain.enums.tax_regime import TaxRegime
from src.domain.errors.fiscal_info_error import (
    FiscalInfoNotFoundError,
    FiscalInfoRequiredError,
    InvalidFiscalDataError,
)
from src.domain.errors.invoice_use_tax_regime_error import (
    NoRegisteredRegimenAllowsInvoiceUseError,
)
from src.domain.errors.regimen_error import (
    NoRegisteredRegimensError,
    RegimenNotRegisteredError,
)
from src.domain.ports.data_encryptor import DataEncryptor
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
from src.domain.services.invoice_use_tax_regime_validator import (
    InvoiceUseTaxRegimeValidator,
)
from src.domain.value_objects.user_id import UserId


class SubmitReceiptUseCase:

    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_job_details_repository: ReceiptJobDetailsRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
        queue_publisher: QueuePublisherPort,
        fiscal_info_repository: FiscalInfoRepositoryPort,
        data_encryptor: DataEncryptor,
    ) -> None:
        self._file_storage = file_storage
        self._receipt_job_details_repository = receipt_job_details_repository
        self._receipt_image_repository = receipt_image_repository
        self._queue_publisher = queue_publisher
        self._fiscal_info_repository = fiscal_info_repository
        self._data_encryptor = data_encryptor
        self._invoice_use_validator = InvoiceUseTaxRegimeValidator()

    async def execute(
        self,
        user_id: UserId,
        grouped_images: dict[str, list[dict[str, bytes | str]]],
        auto_billing: bool,
        uso_cfdi: InvoiceUse | None = None,
        regimen: TaxRegime | None = None,
    ) -> None:

        uso_cfdi_code = uso_cfdi.value if uso_cfdi is not None else None
        regimen_code = regimen.value if regimen is not None else None

        if uso_cfdi is not None:
            await self._validate_invoice_use(
                user_id=user_id,
                uso_cfdi=uso_cfdi,
                regimen=regimen,
            )
        elif regimen is not None:
            await self._ensure_regimen_belongs(
                user_id=user_id, regimen_code=regimen.value
            )

        # Iteramos sobre cada ticket (grupo)
        for group_key, file_details_list in grouped_images.items():
            logger.debug(f"Processing group: {group_key}")

            job_name = JobName.PROCESS_RECEIPT_EXTRACTION

            job_id = await self._receipt_job_details_repository.create(
                user_id=user_id.value, job_name=job_name
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
                    "user_id": user_id.value,
                    "auto_billing": auto_billing,
                    "uso_cfdi": uso_cfdi_code,
                    "regimen": regimen_code,
                },
            )

    async def _validate_invoice_use(
        self,
        user_id: UserId,
        uso_cfdi: InvoiceUse,
        regimen: TaxRegime | None,
    ) -> None:
        """Valida el uso de CFDI contra el tipo de persona y el régimen elegido."""
        try:
            encrypted_rfc = await self._fiscal_info_repository.get_rfc_by_user_id(
                user_id=user_id.value
            )
        except FiscalInfoNotFoundError as exc:
            raise FiscalInfoRequiredError() from exc

        rfc = self._data_encryptor.decrypt(encrypted_rfc)

        try:
            tipo_persona = PersonType.from_rfc(rfc=rfc)
        except ValueError as exc:
            raise InvalidFiscalDataError() from exc

        if regimen is not None:
            await self._ensure_regimen_belongs(
                user_id=user_id,
                regimen_code=regimen.value,
            )
            self._invoice_use_validator.validate(
                uso_cfdi,
                regimen,
                tipo_persona,
            )
            return

        self._invoice_use_validator.validate_invoice_use_for_person_type(
            uso_cfdi,
            tipo_persona,
        )

        regimens = await self._get_registered_regimens(user_id)
        registered_codes = {item["code"] for item in regimens}
        allowed_codes = {
            item.value
            for item in self._invoice_use_validator.allowed_regimes_for_use(uso_cfdi)
        }

        if not (registered_codes & allowed_codes):
            raise NoRegisteredRegimenAllowsInvoiceUseError(
                uso_cfdi.value,
                sorted(registered_codes),
                sorted(allowed_codes),
            )

    async def _ensure_regimen_belongs(self, user_id: UserId, regimen_code: str) -> None:
        """Valida que el régimen elegido pertenezca a los registrados del RFC."""
        regimens = await self._get_registered_regimens(user_id)
        registered_codes = {item["code"] for item in regimens}

        if regimen_code not in registered_codes:
            raise RegimenNotRegisteredError(regimen_code)

    async def _get_registered_regimens(self, user_id: UserId) -> list[dict[str, Any]]:
        regimens = await self._fiscal_info_repository.get_regimens_by_user_id(
            user_id=user_id.value
        )

        if not regimens:
            raise NoRegisteredRegimensError()

        return regimens
