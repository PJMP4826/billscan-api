from typing import Any
from src.domain.enums.job_names import JobName
from src.infrastructure.registries.job_registry import JobRegistry
from src.bootstraps.use_cases_bootstrap import get_process_receipt_extraction_use_case

@JobRegistry.register(JobName.PROCESS_RECEIPT_EXTRACTION)
async def handle_process_receipt_extraction(payload: dict[str, Any]) -> None:
    # Al pasar background_tasks=None, el bootstrap sabe que no estamos en un Request
    # e inyectará el NullQueuePublisher automáticamente.
    use_case = get_process_receipt_extraction_use_case(background_tasks=None)
    
    # Ejecutamos el caso de uso pasando los datos del payload serializado
    await use_case.execute(
        job_id=int(payload["job_id"]),
        user_id=str(payload["user_id"]),
        auto_billing=payload.get("auto_billing", False)
    )