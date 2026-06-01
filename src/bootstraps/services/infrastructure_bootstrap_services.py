from src.config.settings import settings
from src.infrastructure.adapters.http_adapter import HttpClientAdapter
from src.infrastructure.adapters.llm_providers.gemini_multi_modal_llm_adapter import GeminiMultiModalAdapter
from src.infrastructure.services.llama_index_ai_extractor import LlamaIndexAiExtractor

def get_http_client_adapter() -> HttpClientAdapter:
    return HttpClientAdapter()

def get_gemini_multimodal_adapter_llm() -> GeminiMultiModalAdapter:
    return GeminiMultiModalAdapter(
        api_key=settings.google_api_key,
        llm_model_name=settings.llm_gemini_model
    )

def get_llama_index_ai_extractor_service() -> LlamaIndexAiExtractor:
    llm_provider = get_gemini_multimodal_adapter_llm().get_multi_modal_llm_model
    return LlamaIndexAiExtractor(
        http_adapter=get_http_client_adapter(),
        llm_provider=llm_provider
    )