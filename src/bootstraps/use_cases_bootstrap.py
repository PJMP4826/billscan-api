from src.bootstraps.services.infrastructure_bootstrap_services import get_llama_index_ai_extractor_service
from src.application.use_cases.extract_receipt_info_use_case import ExtractReceiptInfoUseCase

def get_extract_receipt_info_use_case() -> ExtractReceiptInfoUseCase:
    extractor = get_llama_index_ai_extractor_service()
    return ExtractReceiptInfoUseCase(
        extractor=extractor
    )