from src.bootstraps.services.infrastructure_bootstrap_services import (
    get_llama_index_ai_extractor_service,
    # get_cloudflare_r2_file_storage_adapter,
    get_background_task_queue_adapter,
    get_disk_file_storage_adapter,
    get_fernet_encryptor,
    get_facturagpt_billing_adapter,
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
    get_receipt_item_repository,
    get_receipt_tax_repository,
    get_receipt_payment_repository,
    get_receipt_billing_detail_repository,
    get_fiscal_info_repository,
    get_reporting_repository,
)
from src.infrastructure.adapters.queue_adapters.background_task_queue_adapter import (
    BackgroundTaskQueueAdapter,
)
from src.infrastructure.adapters.queue_adapters.asyncio_queue_publisher import (
    AsyncioQueuePublisher,
)
from src.application.use_cases.create_fiscal_info_use_case import (
    CreateFiscalInfoUseCase,
)
from src.application.use_cases.initiate_billing_use_case import (
    InitiateBillingUseCase,
)
from src.application.use_cases.get_deductible_expenses_summary_use_case import (
    GetDeductibleExpensesSummaryUseCase,
)
from src.application.use_cases.get_issued_cfdi_summary_use_case import (
    GetIssuedCFDISummaryUseCase,
)
from src.application.use_cases.get_recent_activity_use_case import (
    GetRecentActivityUseCase,
)
from src.application.use_cases.get_receipt_detail_use_case import (
    GetReceiptDetailUseCase,
)

from fastapi import BackgroundTasks


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
        queue_publisher = AsyncioQueuePublisher()

    return ProcessReceiptExtractionUseCase(
        file_storage=get_disk_file_storage_adapter(),
        receipt_repository=get_receipt_repository(),
        receipt_job_details_repository=get_receipt_job_details_repository(),
        receipt_image_repository=get_receipt_image_repository(),
        merchant_repository=get_merchant_repository(),
        item_repository=get_receipt_item_repository(),
        tax_repository=get_receipt_tax_repository(),
        payment_repository=get_receipt_payment_repository(),
        billing_detail_repository=get_receipt_billing_detail_repository(),
        extractor=get_llama_index_ai_extractor_service(),
        queue_publisher=queue_publisher,
    )


def get_create_fiscal_info_use_case() -> CreateFiscalInfoUseCase:
    return CreateFiscalInfoUseCase(
        fiscal_info_repository=get_fiscal_info_repository(),
        encryptor=get_fernet_encryptor(),
    )


def get_initiate_billing_use_case() -> InitiateBillingUseCase:
    return InitiateBillingUseCase(
        billing_provider=get_facturagpt_billing_adapter(),
        billing_detail_repository=get_receipt_billing_detail_repository(),
        receipt_image_repository_port=get_receipt_image_repository(),
        fiscal_info_repository_port=get_fiscal_info_repository(),
        receipt_repository=get_receipt_repository(),
        encryptor=get_fernet_encryptor(),
    )


def get_deductible_expenses_summary_use_case() -> GetDeductibleExpensesSummaryUseCase:
    return GetDeductibleExpensesSummaryUseCase(
        reporting_repository=get_reporting_repository()
    )


def get_issued_cfdi_summary_use_case() -> GetIssuedCFDISummaryUseCase:
    return GetIssuedCFDISummaryUseCase(reporting_repository=get_reporting_repository())


def get_recent_activity_use_case() -> GetRecentActivityUseCase:
    return GetRecentActivityUseCase(reporting_repository=get_reporting_repository())


def get_receipt_detail_use_case() -> GetReceiptDetailUseCase:
    return GetReceiptDetailUseCase(reporting_repository=get_reporting_repository())
