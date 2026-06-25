from src.config.settings import settings
from src.infrastructure.adapters.http_adapter import HttpClientAdapter
from src.infrastructure.adapters.llm_providers.gemini_multi_modal_llm_adapter import (
    GeminiMultiModalAdapter,
)
from src.infrastructure.services.llama_index_ai_extractor import LlamaIndexAiExtractor
from src.infrastructure.adapters.files_storage.cloudflare_r2_file_storage_adapter import (
    CloudFlareR2FileStorageAdapter,
)
from src.infrastructure.adapters.files_storage.disk_file_storage_adapter import (
    DiskFileStorageAdapter,
)
from src.infrastructure.adapters.queue_adapters.background_task_queue_adapter import (
    BackgroundTaskQueueAdapter,
)
from src.infrastructure.adapters.security.fernet_encryptor import FernetEncryptor
from src.infrastructure.adapters.billing_providers.facturagpt_billing_adapter import (
    FacturaGPTBillingAdapter,
)


from fastapi import BackgroundTasks

_facturagpt_billing_adapter_instance: FacturaGPTBillingAdapter | None = None


def get_http_client_adapter() -> HttpClientAdapter:
    return HttpClientAdapter()


def get_gemini_multimodal_adapter_llm() -> GeminiMultiModalAdapter:
    return GeminiMultiModalAdapter(
        api_key=settings.google_api_key, llm_model_name=settings.llm_gemini_model
    )


def get_llama_index_ai_extractor_service() -> LlamaIndexAiExtractor:
    llm_provider = get_gemini_multimodal_adapter_llm().get_multi_modal_llm_model
    return LlamaIndexAiExtractor(
        http_adapter=get_http_client_adapter(), llm_provider=llm_provider
    )


def get_cloudflare_r2_file_storage_adapter() -> CloudFlareR2FileStorageAdapter:
    return CloudFlareR2FileStorageAdapter(
        access_key_id=settings.r2_access_key_id,
        account_id=settings.r2_account_id,
        bucket_name=settings.r2_bucket_name,
        public_base_url=settings.r2_public_base_url,
        secret_access_key=settings.r2_secret_access_key,
    )


def get_disk_file_storage_adapter() -> DiskFileStorageAdapter:
    return DiskFileStorageAdapter()


def get_background_task_queue_adapter(
    background_tasks: BackgroundTasks,
) -> BackgroundTaskQueueAdapter:
    return BackgroundTaskQueueAdapter(background_tasks=background_tasks)


def get_fernet_encryptor() -> FernetEncryptor:
    return FernetEncryptor(encryption_key=settings.encryption_key)


def get_facturagpt_billing_adapter() -> FacturaGPTBillingAdapter:
    global _facturagpt_billing_adapter_instance
    if _facturagpt_billing_adapter_instance is None:
        _facturagpt_billing_adapter_instance = FacturaGPTBillingAdapter(
            api_key=settings.facturagpt_api_key,
            base_url=settings.facturagpt_base_url,
        )
    return _facturagpt_billing_adapter_instance
