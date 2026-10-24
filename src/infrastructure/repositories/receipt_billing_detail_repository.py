from datetime import datetime
import json
from typing import Any

from src.domain.value_objects.billing_data import BillingData
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.domain.ports.repositories.receipt_billing_detail_repository_port import (
    ReceiptBillingDetailRepositoryPort,
)


class ReceiptBillingDetailRepository(ReceiptBillingDetailRepositoryPort):
    """Repositorio para `receipt_billing_details` (relación 1:1 con
    `receipts`, vía PK = receipt_id).

    `insert` crea el registro inicial a partir del `BillingData` extraído
    por el LLM (estado FacturaGPT aún NOT_REQUESTED). Las actualizaciones
    de estado posteriores (vía webhook de FacturaGPT) usan
    `update_billing_status`, que NO requiere un `BillingData` completo y
    se mantiene separado porque llega en un flujo asíncrono distinto.

    `extra_metadata` aquí corresponde a `Receipt.extra_metadata`
    (dict[str, str] | None), NO a `BillingData.billing_metadata` (que se
    guarda en la columna `billing_data`). Ambos se serializan con
    json.dumps() -- mismo caveat de doble-codificación que en
    ReceiptItemRepository si el driver ya adapta dict -> JSONB.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_id: int,
        billing: BillingData | None,
    ) -> None:
        """Crea el registro 1:1 inicial de detalles de facturación.

        Si `billing` es None, se inserta una fila con valores por defecto
        (is_billable=False, billing_status='NOT_REQUESTED') para mantener
        la relación 1:1 consistente y permitir updates posteriores vía
        update_billing_status.
        """
        is_billable = billing.is_billable if billing else False
        has_qr_code = billing.has_qr_code if billing else False
        billing_url = billing.billing_url if billing else None
        barcode = billing.barcode if billing else None
        billing_code = billing.billing_code if billing else None
        expiration_date = billing.expiration_date if billing else None
        billing_metadata_json = (
            json.dumps(billing.billing_metadata)
            if billing and billing.billing_metadata is not None
            else None
        )

        sql = """
            INSERT INTO receipt_billing_details (
                receipt_id,
                is_billable,
                has_qr_code,
                billing_url,
                barcode,
                billing_code,
                expiration_date,
                billing_metadata
            )
            VALUES (
                :receipt_id,
                :is_billable,
                :has_qr_code,
                :billing_url,
                :barcode,
                :billing_code,
                :expiration_date,
                :billing_metadata
            );
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "is_billable": is_billable,
            "has_qr_code": has_qr_code,
            "billing_url": billing_url,
            "barcode": barcode,
            "billing_code": billing_code,
            "expiration_date": expiration_date,
            "billing_metadata": billing_metadata_json,
        }
        await self._db_manager.execute_statement(sql, params)

    async def find_by_receipt_id(self, receipt_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT
                receipt_id,
                is_billable,
                has_qr_code,
                billing_url,
                barcode,
                billing_code,
                expiration_date,
                billing_data,
                extra_metadata,
                uso_cfdi,
                regimen_code,
                facturagpt_session_id,
                billing_status,
                billing_error_code,
                billing_error_message,
                updated_at
            FROM receipt_billing_details
            WHERE receipt_id = :receipt_id;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_id": receipt_id}
        )

    async def set_billing_preferences(
        self,
        receipt_id: int,
        uso_cfdi: str | None = None,
        regimen_code: str | None = None,
    ) -> None:
        """Guarda el uso de CFDI y el régimen elegidos por el cliente.

        Se usa ``COALESCE`` para que los valores ``None`` no pisen lo que ya
        estuviera persistido (útil cuando solo se reintenta con un campo o
        cuando el timbrado hace write-back de los valores efectivos).
        """
        sql = """
            UPDATE receipt_billing_details
            SET uso_cfdi = COALESCE(:uso_cfdi, uso_cfdi),
                regimen_code = COALESCE(:regimen_code, regimen_code),
                updated_at = CURRENT_TIMESTAMP
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "receipt_id": receipt_id,
                "uso_cfdi": uso_cfdi,
                "regimen_code": regimen_code,
            },
        )

    async def update_billing_status(
        self,
        receipt_id: int,
        billing_status: str,
        facturagpt_session_id: str | None = None,
        billing_error_code: str | None = None,
        billing_error_message: str | None = None,
        cfdi_content: dict[str, Any] | None = None,
        completed_at: str | None = None,
    ) -> None:
        """Actualiza el estado de facturación, típicamente desde un
        webhook de FacturaGPT (PENDING, PROCESSING, COMPLETED, FAILED,
        etc. según convención del proyecto).

        `cfdi_summary` (dict crudo del evento factura.completed) se persiste
        en la columna JSONB `cfdi_summary`; `completed_at` en su columna
        timestamptz. Ambos se ignoran si llegan como None (no pisan lo
        existente) — esto hace al UPDATE idempotente ante reintentos.
        """
        cfdi_summary_json = (
            json.dumps(cfdi_content) if cfdi_content is not None else None
        )

        sql = """
            UPDATE receipt_billing_details
            SET billing_status = :billing_status,
                facturagpt_session_id = COALESCE(:facturagpt_session_id, facturagpt_session_id),
                billing_error_code = :billing_error_code,
                billing_error_message = :billing_error_message,
                cfdi_summary = COALESCE(CAST(:cfdi_summary AS JSONB), cfdi_summary),
                completed_at = COALESCE(CAST(:completed_at AS timestamptz), completed_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE receipt_id = :receipt_id;
        """
        completed_at_datetime = None
        if completed_at:
            completed_at_datetime = datetime.fromisoformat(completed_at)

        await self._db_manager.execute_statement(
            sql,
            {
                "receipt_id": receipt_id,
                "billing_status": billing_status,
                "facturagpt_session_id": facturagpt_session_id,
                "billing_error_code": billing_error_code,
                "billing_error_message": billing_error_message,
                "cfdi_summary": cfdi_summary_json,
                "completed_at": completed_at_datetime,
            },
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_billing_details
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
