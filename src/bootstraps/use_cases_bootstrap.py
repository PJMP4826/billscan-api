from fastapi import BackgroundTasks


def get_submit_receipt_use_case(background_tasks: BackgroundTasks):
    from src.application.use_cases.submit_receipt_use_case import SubmitReceiptUseCase
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
        get_background_task_queue_adapter,
    )
    from .repositories.repositories_bootstrap import (
        get_fiscal_info_repository,
        get_receipt_image_repository,
        get_receipt_job_details_repository,
    )

    return SubmitReceiptUseCase(
        file_storage=get_cloudflare_r2_file_storage_adapter(),
        queue_publisher=get_background_task_queue_adapter(
            background_tasks=background_tasks
        ),
        receipt_image_repository=get_receipt_image_repository(),
        receipt_job_details_repository=get_receipt_job_details_repository(),
        fiscal_info_repository=get_fiscal_info_repository(),
    )


def get_process_receipt_extraction_use_case(
    background_tasks: BackgroundTasks | None = None,
):
    from src.application.use_cases.process_receipt_extraction_use_case import (
        ProcessReceiptExtractionUseCase,
    )
    from src.infrastructure.adapters.queue_adapters.background_task_queue_adapter import (
        BackgroundTaskQueueAdapter,
    )
    from src.infrastructure.adapters.queue_adapters.asyncio_queue_publisher import (
        AsyncioQueuePublisher,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
        get_llama_index_ai_extractor_service,
    )
    from .repositories.repositories_bootstrap import (
        get_receipt_repository,
        get_receipt_job_details_repository,
        get_receipt_image_repository,
        get_merchant_repository,
        get_receipt_billing_detail_repository,
    )

    # Si viene desde el controlador HTTP, usamos el real de FastAPI
    if background_tasks is not None:
        queue_publisher = BackgroundTaskQueueAdapter(background_tasks=background_tasks)
    else:
        # Si viene desde el Handler/Worker de fondo, usamos el Null adapter
        queue_publisher = AsyncioQueuePublisher()

    return ProcessReceiptExtractionUseCase(
        file_storage=get_cloudflare_r2_file_storage_adapter(),
        receipt_repository=get_receipt_repository(),
        receipt_job_details_repository=get_receipt_job_details_repository(),
        receipt_image_repository=get_receipt_image_repository(),
        merchant_repository=get_merchant_repository(),
        billing_detail_repository=get_receipt_billing_detail_repository(),
        extractor=get_llama_index_ai_extractor_service(),
        queue_publisher=queue_publisher,
    )


def get_create_fiscal_info_use_case():
    from src.application.use_cases.create_fiscal_info_use_case import (
        CreateFiscalInfoUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_fernet_encryptor,
    )
    from .repositories.repositories_bootstrap import get_fiscal_info_repository

    return CreateFiscalInfoUseCase(
        fiscal_info_repository=get_fiscal_info_repository(),
        encryptor=get_fernet_encryptor(),
    )


def get_create_fiscal_info_from_csf_use_case():
    from src.application.use_cases.create_fiscal_info_from_csf_use_case import (
        CreateFiscalInfoFromCsfUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_fernet_encryptor,
        get_billing_customer_info_extractor,
    )
    from .repositories.repositories_bootstrap import get_fiscal_info_repository

    return CreateFiscalInfoFromCsfUseCase(
        fiscal_info_repository=get_fiscal_info_repository(),
        encryptor=get_fernet_encryptor(),
        extractor=get_billing_customer_info_extractor(),
    )


def get_user_fiscal_info_use_case():
    from src.application.use_cases.get_user_fiscal_info_use_case import (
        GetUserFiscalInfoUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_fernet_encryptor,
    )
    from .repositories.repositories_bootstrap import get_fiscal_info_repository

    return GetUserFiscalInfoUseCase(
        fiscal_info_repository=get_fiscal_info_repository(),
        encryptor=get_fernet_encryptor(),
    )


def get_user_regimens_use_case():
    from src.application.use_cases.get_user_regimens_use_case import (
        GetUserRegimensUseCase,
    )
    from .repositories.repositories_bootstrap import get_fiscal_info_repository

    return GetUserRegimensUseCase(
        fiscal_info_repository=get_fiscal_info_repository(),
    )


def get_initiate_billing_use_case():
    from src.application.use_cases.initiate_billing_use_case import (
        InitiateBillingUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_facturagpt_billing_adapter,
        get_fernet_encryptor,
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import (
        get_receipt_billing_detail_repository,
        get_receipt_image_repository,
        get_fiscal_info_repository,
        get_receipt_repository,
    )

    return InitiateBillingUseCase(
        billing_provider=get_facturagpt_billing_adapter(),
        billing_detail_repository=get_receipt_billing_detail_repository(),
        receipt_image_repository_port=get_receipt_image_repository(),
        fiscal_info_repository_port=get_fiscal_info_repository(),
        receipt_repository=get_receipt_repository(),
        encryptor=get_fernet_encryptor(),
        file_storage=get_cloudflare_r2_file_storage_adapter(),
    )


def get_completed_billing_summary_use_case():
    from src.application.use_cases.get_completed_billing_summary_use_case import (
        GetCompletedBillingSummaryUseCase,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetCompletedBillingSummaryUseCase(
        reporting_repository=get_reporting_repository()
    )


def get_receipt_count_summary_use_case():
    from src.application.use_cases.get_receipt_count_summary_use_case import (
        GetReceiptCountSummaryUseCase,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetReceiptCountSummaryUseCase(
        reporting_repository=get_reporting_repository()
    )


def get_receipt_list_use_case():
    from src.application.use_cases.get_receipt_list_use_case import (
        GetReceiptListUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetReceiptListUseCase(
        reporting_repository=get_reporting_repository(),
        file_storage=get_cloudflare_r2_file_storage_adapter(),
    )


def get_cfdi_list_use_case():
    from src.application.use_cases.get_cfdi_list_use_case import (
        GetCfdiListUseCase,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetCfdiListUseCase(reporting_repository=get_reporting_repository())


def get_cfdi_detail_use_case():
    from src.application.use_cases.get_cfdi_detail_use_case import (
        GetCfdiDetailUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetCfdiDetailUseCase(
        file_storage=get_cloudflare_r2_file_storage_adapter(),
        reporting_repository=get_reporting_repository(),
    )


def get_recent_activity_use_case():
    from src.application.use_cases.get_recent_activity_use_case import (
        GetRecentActivityUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import get_reporting_repository

    return GetRecentActivityUseCase(
        file_storage=get_cloudflare_r2_file_storage_adapter(),
        reporting_repository=get_reporting_repository(),
    )


def get_receipt_detail_use_case():
    from src.application.use_cases.get_receipt_detail_use_case import (
        GetReceiptDetailUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import (
        get_receipt_repository,
        get_receipt_image_repository,
    )

    return GetReceiptDetailUseCase(
        file_storage=get_cloudflare_r2_file_storage_adapter(),
        receipt_repository=get_receipt_repository(),
        receipt_image_repository=get_receipt_image_repository(),
    )


def get_process_facturagpt_webhook_use_case():
    """Use case worker (sin BackgroundTasks): corre fuera del request HTTP,
    invocado por el handler de cola. Recibe solo `{"idempotency_key": ...}`
    y relee el payload crudo desde BD (store-before-process)."""
    from src.application.use_cases.process_facturagpt_webhook_use_case import (
        ProcessFacturaGPTWebhookUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_facturagpt_webhook_handler,
        get_facturagpt_billing_adapter,
        get_cloudflare_r2_file_storage_adapter,
    )
    from .repositories.repositories_bootstrap import (
        get_facturagpt_webhook_repository,
        get_receipt_repository,
        get_receipt_billing_detail_repository,
        get_billing_file_repository,
    )

    return ProcessFacturaGPTWebhookUseCase(
        webhook_repository=get_facturagpt_webhook_repository(),
        receipt_repository=get_receipt_repository(),
        billing_detail_repository=get_receipt_billing_detail_repository(),
        billing_file_repository=get_billing_file_repository(),
        webhook_handler=get_facturagpt_webhook_handler(),
        billing_provider=get_facturagpt_billing_adapter(),
        file_storage=get_cloudflare_r2_file_storage_adapter(),
    )


def get_receive_facturagpt_webhook_use_case(background_tasks: BackgroundTasks):
    """Use case de ingesta HTTP: orquesta firma + store-before-process +
    encolado. Se construye por request porque el queue_publisher vive en los
    BackgroundTasks de ese request (corre justo después de responder 200)."""
    from src.application.use_cases.receive_facturagpt_webhook_use_case import (
        ReceiveFacturaGPTWebhookUseCase,
    )
    from src.bootstraps.services.infrastructure_bootstrap_services import (
        get_facturagpt_webhook_handler,
        get_background_task_queue_adapter,
    )
    from .repositories.repositories_bootstrap import (
        get_facturagpt_webhook_repository,
    )

    return ReceiveFacturaGPTWebhookUseCase(
        webhook_handler=get_facturagpt_webhook_handler(),
        webhook_repository=get_facturagpt_webhook_repository(),
        queue_publisher=get_background_task_queue_adapter(
            background_tasks=background_tasks
        ),
    )
