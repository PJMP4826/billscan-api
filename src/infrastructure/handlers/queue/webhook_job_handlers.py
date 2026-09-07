"""
Handlers de cola para jobs derivados de webhooks (FacturaGPT y afines).

Registrados vía JobRegistry.register — el módulo DEBE importarse al arrancar
(en main.py) para que el registro exista antes de que cualquier adaptador de
cola intente despachar el job.
"""

from typing import Any

from src.domain.enums.job_names import JobName
from src.infrastructure.registries.job_registry import JobRegistry
from src.bootstraps.use_cases_bootstrap import (
    get_process_facturagpt_webhook_use_case,
)


@JobRegistry.register(JobName.PROCESS_FACTURAGPT_WEBHOOK)
async def handle_process_facturagpt_webhook(payload: dict[str, Any]) -> None:
    """
    Worker del webhook de FacturaGPT. Corre en background (BackgroundTasks
    del request o AsyncioQueue para jobs encadenados), SIEMPRE después de que
    el endpoint ya respondió 200.

    payload solo trae {"idempotency_key": ...}: el payload crudo se relee de
    `facturagpt_webhooks` (store-before-process), lo que hace el procesamiento
    reproducible ante reintentos y reconciliación.
    """
    use_case = get_process_facturagpt_webhook_use_case()

    await use_case.execute(payload=payload)
