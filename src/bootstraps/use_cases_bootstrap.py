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
from src.application.use_cases.process_receipt_extraction_use_case import (
    ProcessReceiptExtractionUseCase,
)
from .repositories.repositories_bootstrap import (
    get_receipt_image_repository,
    get_receipt_job_details_repository,
    get_receipt_repository,
    get_merchant_repository,
)
from src.infrastructure.adapters.queue_adapters.background_task_queue_adapter import (
    BackgroundTaskQueueAdapter,
)
from src.infrastructure.adapters.queue_adapters.null_queue_publisher import (
    NullQueuePublisher,
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


def get_process_receipt_extraction_use_case(
    background_tasks: BackgroundTasks | None = None,
) -> ProcessReceiptExtractionUseCase:

    # Si viene desde el controlador HTTP, usamos el real de FastAPI
    if background_tasks is not None:
        queue_publisher = BackgroundTaskQueueAdapter(background_tasks=background_tasks)
    else:
        # Si viene desde el Handler/Worker de fondo, usamos el Null adapter
        queue_publisher = NullQueuePublisher()

    return ProcessReceiptExtractionUseCase(
        file_storage=get_disk_file_storage_adapter(),
        receipt_repository=get_receipt_repository(),
        receipt_job_details_repository=get_receipt_job_details_repository(),
        receipt_image_repository=get_receipt_image_repository(),
        merchant_repository=get_merchant_repository(),
        extractor=get_llama_index_ai_extractor_service(),
        queue_publisher=queue_publisher,
    )
