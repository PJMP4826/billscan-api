from src.config.settings import settings
from fastapi import BackgroundTasks

_facturagpt_billing_adapter_instance = None
_facturagpt_webhook_handler_instance = None


def get_http_client_adapter():
    from src.infrastructure.adapters.http_adapter import HttpClientAdapter

    return HttpClientAdapter()


def get_gemini_multimodal_adapter_llm():
    from src.infrastructure.adapters.llm_providers.gemini_multi_modal_llm_adapter import (
        GeminiMultiModalAdapter,
    )

    return GeminiMultiModalAdapter(
        api_key=settings.google_api_key, llm_model_name=settings.llm_gemini_model
    )


def get_llama_index_ai_extractor_service():
    from src.infrastructure.services.llama_index_ai_extractor import (
        LlamaIndexAiExtractor,
    )

    llm_provider = get_gemini_multimodal_adapter_llm().get_multi_modal_llm_model
    return LlamaIndexAiExtractor(
        http_adapter=get_http_client_adapter(), llm_provider=llm_provider
    )


def get_billing_customer_info_extractor():
    """Extractor de datos fiscales a partir de una CSF (PDF, JPG o PNG)."""
    from csf_scraper import GeminiImageReader

    from src.infrastructure.adapters.billing_customer_info_extractor import (
        BillingCustomerInfoExtractor,
    )

    image_reader = GeminiImageReader(
        api_key=settings.google_api_key,
        model_name=settings.llm_gemini_model,
    )
    return BillingCustomerInfoExtractor(image_reader=image_reader)


def get_cloudflare_r2_file_storage_adapter():
    from src.infrastructure.adapters.files_storage.cloudflare_r2_file_storage_adapter import (
        CloudFlareR2FileStorageAdapter,
    )

    return CloudFlareR2FileStorageAdapter(
        access_key_id=settings.r2_access_key_id,
        account_id=settings.r2_account_id,
        bucket_name=settings.r2_bucket_name,
        public_base_url=settings.r2_public_base_url,
        secret_access_key=settings.r2_secret_access_key,
    )


def get_disk_file_storage_adapter():
    from src.infrastructure.adapters.files_storage.disk_file_storage_adapter import (
        DiskFileStorageAdapter,
    )

    return DiskFileStorageAdapter()


def get_background_task_queue_adapter(background_tasks: BackgroundTasks):
    from src.infrastructure.adapters.queue_adapters.background_task_queue_adapter import (
        BackgroundTaskQueueAdapter,
    )

    return BackgroundTaskQueueAdapter(background_tasks=background_tasks)


def get_fernet_encryptor():
    from src.infrastructure.adapters.security.fernet_encryptor import FernetEncryptor

    return FernetEncryptor(encryption_key=settings.encryption_key)


def get_facturagpt_billing_adapter():
    global _facturagpt_billing_adapter_instance
    if _facturagpt_billing_adapter_instance is None:
        from src.infrastructure.adapters.billing_providers.facturagpt_billing_adapter import (
            FacturaGPTBillingAdapter,
        )

        _facturagpt_billing_adapter_instance = FacturaGPTBillingAdapter(
            api_key=settings.facturagpt_api_key,
            base_url=settings.facturagpt_base_url,
        )
    return _facturagpt_billing_adapter_instance


def get_facturagpt_webhook_handler():
    """Handler singleton de verificación/firma + parseo de webhooks.

    Exige `settings.facturagpt_webhook_secret` (whsec_...): se valida en el
    primer uso (cuando llega un webhook o al armar el worker), no al arrancar,
    para no romper el boot si el entorno aún no lo define.
    """
    global _facturagpt_webhook_handler_instance
    if _facturagpt_webhook_handler_instance is None:
        if not settings.facturagpt_webhook_secret:
            raise RuntimeError(
                "Falta configurar facturagpt_webhook_secret (whsec_...) "
                "en el entorno para procesar webhooks de FacturaGPT."
            )
        from src.infrastructure.adapters.billing_providers.facturagpt_webhook_handler import (
            FacturaGPTWebhookHandler,
        )

        _facturagpt_webhook_handler_instance = FacturaGPTWebhookHandler(
            webhook_secret=settings.facturagpt_webhook_secret
        )
    return _facturagpt_webhook_handler_instance
