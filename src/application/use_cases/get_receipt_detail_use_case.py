from src.application.dtos.receipt_detail_dto import ReceiptDetailDto
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.ports.repositories.receipt_repository_port import (
    ReceiptRepositoryPort,
)


class GetReceiptDetailUseCase:
    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_repository: ReceiptRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
    ) -> None:
        self._file_storage = file_storage
        self._receipt_repository = receipt_repository
        self._receipt_image_repository = receipt_image_repository

    async def execute(self, receipt_uuid: str) -> ReceiptDetailDto:
        receipt = await self._receipt_repository.find_by_uuid(receipt_uuid)
        file_key = await self._receipt_image_repository.find_key_by_receipt_uuid(
            receipt_uuid=receipt.receipt_uuid
        )
        file_url = await self._file_storage.get_url(str(file_key))

        return ReceiptDetailDto(receipt=receipt, file_url=file_url)
