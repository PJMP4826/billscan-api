"""
ProcessFacturaGPTWebhookUseCase — procesamiento idempotente de webhooks.

Corre en background (worker de cola), DESPUÉS de que el endpoint ya respondió
200 al proveedor. Por eso:

- Recibe SOLO un identificador (`idempotency_key`), nunca el payload completo:
  el payload crudo ya quedó persistido en `facturagpt_webhooks` en el momento
  del recibo (store-before-process). Esto hace el flujo tolerante a fallos:
  aunque el worker muera, el evento está en BD y puede reintentarse (red de
  FacturaGPT o reconciliación) sin volver a recibir el webhook.

Idempotencia:
- `find_by_key(...)`: si `processed_at` ya está seteado, no se hace nada
  (el evento ya fue aplicado por una corrida anterior).
- `mark_processed(...)`: UPDATE condicional al final. Si dos workers
  compiten, solo uno gana.
- La descarga + upload a storage usan claves determinísticas (`PUT` de S3
  sobrescribe), y el INSERT en `billing_files` se salta tipos ya presentes.

Convención clave: `external_id` que devuelve FacturaGPT == `receipt.receipt_uuid`.
"""

import json
import re
from typing import Any

from src.config.logger import logger
from src.application.dtos.cfdi import CfdiDto
from src.application.dtos.invoice_result_dto import InvoiceResult

from src.domain.enums.billing_file_type import BillingFileType
from src.domain.enums.billing_status import BillingStatus
from src.domain.enums.billing_webhook_event_type import BillingWebHookEventType
from src.domain.ports.billing_provider import BillingProviderPort
from src.domain.ports.billing_webhook_handler_port import BillingWebhookHandlerPort
from src.domain.ports.file_storage_port import FileStoragePort
from src.domain.ports.repositories.billing_file_repository_port import (
    BillingFileRepositoryPort,
)
from src.domain.ports.repositories.facturagpt_webhook_repository_port import (
    FacturaGPTWebhookRepositoryPort,
)
from src.domain.ports.repositories.receipt_billing_detail_repository_port import (
    ReceiptBillingDetailRepositoryPort,
)
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort
from src.infrastructure.adapters.cfdi_parser import CfdiParser
from src.shared.errors.billing_exceptions import BillingProviderError

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_filename(value: str | None, fallback: str) -> str:
    """Normaliza el folio fiscal a caracteres seguros para una key de storage."""
    if not value:
        return fallback
    cleaned = _SAFE_CHARS.sub("_", value).strip("_")
    return cleaned if cleaned else fallback


class ProcessFacturaGPTWebhookUseCase:
    def __init__(
        self,
        webhook_repository: FacturaGPTWebhookRepositoryPort,
        receipt_repository: ReceiptRepositoryPort,
        billing_detail_repository: ReceiptBillingDetailRepositoryPort,
        billing_file_repository: BillingFileRepositoryPort,
        webhook_handler: BillingWebhookHandlerPort,
        billing_provider: BillingProviderPort,
        file_storage: FileStoragePort,
    ) -> None:
        self._webhook_repository = webhook_repository
        self._receipt_repository = receipt_repository
        self._billing_detail_repository = billing_detail_repository
        self._billing_file_repository = billing_file_repository
        self._webhook_handler = webhook_handler
        self._billing_provider = billing_provider
        self._file_storage = file_storage

    async def execute(self, payload: dict[str, Any]) -> None:
        idempotency_key = str(payload["idempotency_key"])

        try:
            await self._process(idempotency_key)
        except Exception as exc:
            # No se marca processed_at: el evento queda pendiente (NULL) y un
            # reintento (duplicado de red o job de reconciliación) lo retoma.
            logger.error(
                "Error procesando webhook FacturaGPT idempotency_key=%s: %s",
                idempotency_key,
                exc,
                exc_info=True,
            )
            try:
                await self._webhook_repository.update_error(
                    idempotency_key=idempotency_key,
                    error_message=str(exc)[:2000],
                )
            except (
                Exception
            ) as inner_exc:  # noqa: BLE001 - nunca ocultar el error original
                logger.error(
                    "No se pudo registrar el error del webhook %s: %s",
                    idempotency_key,
                    inner_exc,
                )

    async def _process(self, idempotency_key: str) -> None:
        webhook_row = await self._webhook_repository.find_by_key(
            idempotency_key=idempotency_key
        )
        if webhook_row is None:
            logger.warning(
                "Webhook %s no encontrado en BD (¿se limpió?). Nada que procesar.",
                idempotency_key,
            )
            return

        if webhook_row.get("processed_at") is not None:
            logger.info(
                "Webhook %s ya fue procesado (%s); entrega duplicada ignorada.",
                idempotency_key,
                webhook_row.get("processed_at"),
            )
            return

        raw_payload = webhook_row["payload"]
        if isinstance(raw_payload, str):
            raw_payload = json.loads(raw_payload)

        # Re-parsea el payload crudo (fuente de verdad = BD, no el worker).
        invoice_result = self._webhook_handler.parse_event(raw_payload)

        # El worker solo sabe aplicar eventos por-receipt de FacturaGPT.
        event = invoice_result.event
        if event not in (
            BillingWebHookEventType.COMPLETED,
            BillingWebHookEventType.FAILED,
        ):
            logger.warning(
                "Webhook %s con evento '%s' no procesable por el worker; se omite.",
                idempotency_key,
            )
            await self._webhook_repository.mark_processed(
                idempotency_key=idempotency_key
            )
            return

        # external_id == receipt_uuid (lo fija InitiateBillingUseCase).
        receipt_uuid = invoice_result.external_id
        if not receipt_uuid:
            raise ValueError("El webhook no trae external_id para asociar al receipt")

        receipt_id = await self._receipt_repository.find_id_by_uuid(
            receipt_uuid=receipt_uuid
        )
        if receipt_id is None:
            # Se deja processed_at en NULL: si el receipt aparece después
            # (reorden de eventos), un reintento lo resuelve.
            raise ValueError(
                f"No existe receipt con receipt_uuid='{receipt_uuid}' "
                f"(external_id del webhook {idempotency_key})"
            )

        if event is BillingWebHookEventType.COMPLETED:
            await self._apply_completed(
                receipt_id=receipt_id,
                idempotency_key=idempotency_key,
                invoice_result=invoice_result,
            )
        else:  # FAILED
            await self._apply_failed(
                receipt_id=receipt_id,
                invoice_result=invoice_result,
            )

        # Único punto de verdad sobre "este webhook ya se aplicó".
        won = await self._webhook_repository.mark_processed(
            idempotency_key=idempotency_key
        )
        if not won:
            logger.warning(
                "Webhook %s ya fue marcado como procesado por otra corrida.",
                idempotency_key,
            )

    # Evento factura.completed
    async def _apply_completed(
        self,
        receipt_id: int,
        idempotency_key: str,
        invoice_result: InvoiceResult,
    ) -> None:
        files = invoice_result.files
        folio = (
            invoice_result.cfdi_summary.folio_fiscal
            if invoice_result.cfdi_summary is not None
            else None
        )

        # 1) Descargar el XML y parsearlo (necesario para cfdi_summary).
        xml_content: bytes | None = None
        xml_mime_type = BillingFileType.XML.mime_type
        cfdi_content: CfdiDto | None = None
        if files and files.xml_url:
            xml_content, xml_mime_type = await self._download_invoce_content(
                url=files.xml_url
            )
            cfdi_content = CfdiParser.parse_bytes(xml_content=xml_content)

        # 2) Persistir PRIMERO el resultado de facturación: es lo que el
        #    cliente ve en la UI. Si la subida de archivos falla después, el
        #    estado ya quedó aplicado y el reintento solo completará archivos.
        await self._billing_detail_repository.update_billing_status(
            receipt_id=receipt_id,
            billing_status=BillingStatus.COMPLETED.value,
            facturagpt_session_id=invoice_result.session_id,
            cfdi_content=cfdi_content.to_dict() if cfdi_content is not None else None,
            completed_at=invoice_result.completed_at,
        )

        # 3) Subir XML/PDF con claves determinísticas (idempotente).
        xml_key = pdf_key = None
        if xml_content is not None:
            xml_key = await self._store_invoice_file(
                content_data=xml_content,
                mime_type=xml_mime_type,
                file_type=BillingFileType.XML,
                folio=folio,
            )

        if files and files.pdf_url:
            pdf_content, pdf_mime_type = await self._download_invoce_content(
                url=files.pdf_url
            )
            pdf_key = await self._store_invoice_file(
                content_data=pdf_content,
                mime_type=pdf_mime_type,
                file_type=BillingFileType.PDF,
                folio=folio,
            )

        # 4) Referenciar en billing_files (solo tipos que falten → idempotente).
        await self._insert_missing_files(
            receipt_id=receipt_id,
            xml_key=xml_key,
            pdf_key=pdf_key,
        )

        logger.info(
            "Webhook %s aplicado: receipt %s marcado como COMPLETED (xml=%s, pdf=%s).",
            idempotency_key,
            receipt_id,
            xml_key,
            pdf_key,
        )

    async def _download_invoce_content(self, url: str) -> tuple[bytes, str]:
        return await self._billing_provider.download_invoice_file(url)

    async def _store_invoice_file(
        self,
        content_data: bytes,
        mime_type: str,
        file_type: BillingFileType,
        folio: str | None,
    ) -> str:
        """Descarga (provider) → sube a storage con key determinística.

        Si la descarga falla se lanza la excepción: el evento queda pendiente
        (processed_at NULL) y el reintento vuelve a intentar aquí sin dejar
        estados a medias (el upload anterior con la misma key se sobrescribe).
        """
        base = _safe_filename(folio, "factura")
        key = f"{base}.{file_type.extension}"

        if "text/html" in mime_type:
            logger.error(
                "FacturaGPT devolvió HTML en vez de archivo (url=%s, content_type=%s). ",
                mime_type,
            )
            raise BillingProviderError(
                "El proxy de descarga devolvió HTML en vez del archivo de factura."
            )

        await self._file_storage.upload(key=key, data=content_data, mime_type=mime_type)
        logger.info("Archivo %s del CFDI almacenado en key='%s'", file_type.value, key)
        return key

    async def _insert_missing_files(
        self,
        receipt_id: int,
        xml_key: str | None,
        pdf_key: str | None,
    ) -> None:
        if xml_key is None and pdf_key is None:
            return

        existing = await self._billing_file_repository.find_by_receipt_id(receipt_id)
        existing_types = {str(row.get("file_type")).upper() for row in existing}

        if xml_key and BillingFileType.XML.value not in existing_types:
            await self._billing_file_repository.insert(
                receipt_id=receipt_id,
                file_type=BillingFileType.XML.value,
                file_key=xml_key,
                mime_type=BillingFileType.XML.mime_type,
            )
        if pdf_key and BillingFileType.PDF.value not in existing_types:
            await self._billing_file_repository.insert(
                receipt_id=receipt_id,
                file_type=BillingFileType.PDF.value,
                file_key=pdf_key,
                mime_type=BillingFileType.PDF.mime_type,
            )

    # Evento factura.failed
    async def _apply_failed(
        self, receipt_id: int, invoice_result: InvoiceResult
    ) -> None:
        await self._billing_detail_repository.update_billing_status(
            receipt_id=receipt_id,
            billing_status=BillingStatus.FAILED.value,
            facturagpt_session_id=invoice_result.session_id,
            billing_error_code=invoice_result.error_code,
            billing_error_message=invoice_result.error_message,
        )
        logger.info(
            "Webhook fallido aplicado: receipt %s -> FAILED (%s: %s)",
            receipt_id,
            invoice_result.error_code,
            invoice_result.error_message,
        )
