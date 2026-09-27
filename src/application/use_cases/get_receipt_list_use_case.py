from src.application.dtos.receipt_list_item_dto import ReceiptListItemResponse
from src.application.dtos.receipt_list_response_dto import ReceiptListResponse
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)


class GetReceiptListUseCase:
    def __init__(
        self,
        reporting_repository: ReportingRepositoryPort,
        file_storage: FileStoragePort,
    ) -> None:
        self._reporting_repository = reporting_repository
        self._file_storage = file_storage

    async def execute(self, page: int = 1, page_size: int = 20) -> ReceiptListResponse:
        data = await self._reporting_repository.get_receipt_list(page, page_size)

        items = [
            ReceiptListItemResponse(
                receipt_uuid=item.receipt_uuid,
                merchant_name=item.merchant_name,
                registered_at=item.registered_at,
                total=item.total,
                status=item.status,
                file_url=await self._file_storage.get_url(item.file_key),
            )
            for item in data.items
        ]

        return ReceiptListResponse(
            items=items,
            total=data.total,
            page=data.page,
            page_size=data.page_size,
        )
