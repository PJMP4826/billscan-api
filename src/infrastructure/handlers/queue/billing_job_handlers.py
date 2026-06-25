from typing import Any
from src.domain.enums.job_names import JobName
from src.infrastructure.registries.job_registry import JobRegistry
from src.bootstraps.use_cases_bootstrap import get_initiate_billing_use_case


@JobRegistry.register(JobName.INITIATE_BILLING)
async def handle_billing_receipt_process(payload: dict[str, Any]) -> None:
    use_case = get_initiate_billing_use_case()

    await use_case.execute(payload=payload)
