from src.bootstraps.services.infrastructure_bootstrap_services import (
    get_llama_index_ai_extractor_service,
    # get_cloudflare_r2_file_storage_adapter,
    get_background_task_queue_adapter,
    get_disk_file_storage_adapter,
)
from src.application.use_cases.extract_receipt_info_use_case import (
    ExtractReceiptInfoUseCase,
)
from src.application.use_cases.submit_receipt_use_case import SubmitReceiptUseCase
from .repositories.repositories_bootstrap import (
    get_receipt_image_repository,
    get_receipt_job_details_repository,
)

from fastapi import BackgroundTasks


def get_extract_receipt_info_use_case() -> ExtractReceiptInfoUseCase:
    extractor = get_llama_index_ai_extractor_service()
    return ExtractReceiptInfoUseCase(extractor=extractor)


def get_submit_receipt_use_case(
    background_tasks: BackgroundTasks,
) -> SubmitReceiptUseCase:
    return SubmitReceiptUseCase(
        file_storage=get_disk_file_storage_adapter(),
        queue_publisher=get_background_task_queue_adapter(
            background_tasks=background_tasks
        ),
        receipt_image_repository=get_receipt_image_repository(),
        receipt_job_details_repository=get_receipt_job_details_repository(),
    )
