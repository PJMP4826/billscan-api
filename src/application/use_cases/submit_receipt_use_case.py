import uuid

from src.config.logger import logger
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.queue_publisher_port import QueuePublisherPort
from src.domain.ports.repositories.receipt_job_details_repository_port import (
    ReceiptJobDetailsRepositoryPort,
)
from src.domain.ports.repositories.receipt_image_repository_port import (
    ReceiptImageRepositoryPort,
)
from src.domain.enums.job_names import JobName


class SubmitReceiptUseCase:

    def __init__(
        self,
        file_storage: FileStoragePort,
        receipt_job_details_repository: ReceiptJobDetailsRepositoryPort,
        receipt_image_repository: ReceiptImageRepositoryPort,
        queue_publisher: QueuePublisherPort,
    ) -> None:
        self._file_storage = file_storage
        self._receipt_job_details_repository = receipt_job_details_repository
        self._receipt_image_repository = receipt_image_repository
        self._queue_publisher = queue_publisher

    async def execute(
        self, user_id: str, grouped_images: dict[str, list[dict[str, bytes | str]]]
    ) -> None:

        # Iteramos sobre cada ticket (grupo)
        for group_key, file_details_list in grouped_images.items():
            logger.debug(f"Processing group: {group_key}")\
            
            job_name = JobName.PROCESS_RECEIPT_EXTRACTION

            job_id = await self._receipt_job_details_repository.create(user_id=user_id, job_name=job_name)

            for page_idx, item in enumerate(file_details_list, start=1):

                file_data = item["file"]
                if not isinstance(file_data, bytes):
                    raise TypeError(
                        f"Se esperaba bytes, pero se recibió {type(file_data).__name__}"
                    )

                file_key = uuid.uuid4().hex
                mime_file_type = str(item["mime"])
                image_url = await self._file_storage.upload(
                    key=file_key,
                    data=file_data,
                    mime_type=mime_file_type,
                )

                await self._receipt_image_repository.insert(
                    receipt_job_id=job_id,
                    file_key=file_key,
                    file_url=image_url,
                    mime_type=mime_file_type,
                    page_number=page_idx,
                )

            self._queue_publisher.enqueue_job(
                job_name=job_name,
                payload={"job_id": job_id},
            )
