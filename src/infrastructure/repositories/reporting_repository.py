from decimal import Decimal
from typing import Any

from src.application.dtos.cfdi.cfdi_dto import CfdiDto
from src.application.dtos.cfdi_response_dto import CfdiResponseDto
from src.application.dtos.invoice_files_dto import InvoiceFiles
from src.domain.enums.billing_status import BillingStatus
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.application.dtos.cfdi import CfdiListItem, CfdiListResponse
from src.application.dtos.completed_billing_summary_dto import (
    CompletedBillingSummary,
)
from src.application.dtos.receipt_count_summary_dto import ReceiptCountSummary
from src.application.dtos.receipt_list_item_dto import ReceiptListItemData
from src.application.dtos.receipt_list_response_dto import ReceiptListData
from src.domain.ports.repositories.reporting_repository_port import (
    ReportingRepositoryPort,
)
from src.infrastructure.database.utils.row_parsers import parse_row_to_str


class PostgresReportingRepository(ReportingRepositoryPort):
    """
    Read-side repository for dashboard and reporting queries.
    These are cross-domain projections — they do not belong to any
    single aggregate. Raw SQL is intentional here.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    _PERIOD_FILTERS: dict[str, str] = {
        "month": "DATE_TRUNC('month', r.created_at) = DATE_TRUNC('month', CURRENT_DATE)",
        "year": "DATE_TRUNC('year', r.created_at) = DATE_TRUNC('year', CURRENT_DATE)",
        "3years": "r.created_at >= CURRENT_DATE - INTERVAL '3 years'",
        "5years": "r.created_at >= CURRENT_DATE - INTERVAL '5 years'",
    }

    async def get_completed_billing_summary(
        self, period: str = "month"
    ) -> CompletedBillingSummary:
        period_filter = self._PERIOD_FILTERS.get(period)
        if period_filter is None:
            raise ValueError(
                f"Periodo inválido: '{period}'. "
                f"Opciones válidas: {', '.join(self._PERIOD_FILTERS)}"
            )

        sql = f"""
            SELECT
                COALESCE(SUM(r.total), 0)  AS total_facturado,
                COUNT(DISTINCT r.id)       AS facturas_generadas
            FROM receipts r
            INNER JOIN receipt_billing_details re_bi_d
                ON re_bi_d.receipt_id = r.id
            INNER JOIN receipt_jobs_details re_job_d
                ON re_job_d.receipt_id = r.id
            WHERE re_bi_d.is_billable = TRUE
              AND re_bi_d.billing_status = 'COMPLETED'
              AND re_job_d.status = 'COMPLETED'
              AND {period_filter};
        """
        row = await self._db_manager.execute_sql_query_fetch_first(sql, {})

        if not row:
            raise ValueError("Error obteniendo resumen de facturación")

        return CompletedBillingSummary(
            total_billed=Decimal(str(row["total_facturado"])),
            invoices_generated=int(row["facturas_generadas"]),
            period=period,
        )

    async def get_receipt_count_summary(self) -> ReceiptCountSummary:
        sql = """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE rbd.is_billable = TRUE) AS billable,
                COUNT(*) FILTER (
                    WHERE rbd.receipt_id IS NULL
                       OR rbd.is_billable = FALSE
                ) AS non_billable,
                COALESCE(SUM(r.total), 0) AS total_spent
            FROM receipts r
            LEFT JOIN receipt_billing_details rbd
                   ON rbd.receipt_id = r.id;
        """
        row = await self._db_manager.execute_sql_query_fetch_first(sql, {})

        if not row:
            raise ValueError("Error obteniendo resumen de receipts")

        return ReceiptCountSummary(
            total=int(row["total"]),
            billable=int(row["billable"]),
            non_billable=int(row["non_billable"]),
            total_spent=Decimal(str(row["total_spent"])),
        )

    async def get_receipt_list(
        self, page: int = 1, page_size: int = 20
    ) -> ReceiptListData:
        offset = (page - 1) * page_size

        count_sql = """
            SELECT COUNT(*) AS total
            FROM receipts r;
        """
        count_row = await self._db_manager.execute_sql_query_fetch_first(count_sql, {})
        total = int(count_row["total"]) if count_row else 0

        sql = """
            SELECT
                r.receipt_uuid,
                m.name AS merchant_name,
                TO_CHAR(r.created_at, 'YYYY-MM-DD HH24:MI:SS') AS registered_at,
                r.total,
                CASE
                    WHEN rbd.receipt_id IS NULL
                      OR rbd.billing_status IS NULL
                      OR rbd.billing_status = 'NOT_REQUESTED'
                    THEN (
                        SELECT rjd.status
                        FROM receipt_jobs_details rjd
                        WHERE rjd.receipt_id = r.id
                        ORDER BY rjd.created_at DESC
                        LIMIT 1
                    )
                    ELSE rbd.billing_status
                END AS "status",
                rimg.file_key
            FROM receipts r
            LEFT JOIN merchants m
                    ON r.merchant_id = m.id
            LEFT JOIN receipt_billing_details rbd
                    ON rbd.receipt_id = r.id
            INNER JOIN receipt_images rimg
                    ON rimg.receipt_id = r.id
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset;
        """
        rows = await self._db_manager.execute_sql_query_fetch_all(
            sql, {"limit": page_size, "offset": offset}
        )

        items = [
            ReceiptListItemData(
                receipt_uuid=row["receipt_uuid"],
                merchant_name=row["merchant_name"],
                registered_at=row["registered_at"],
                total=Decimal(str(row["total"])),
                status=BillingStatus(row["status"] or "UNKNOWN"),
                file_key=row["file_key"],
            )
            for row in rows
        ]

        return ReceiptListData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_recent_activity(
        self,
        receipt_uuid: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        conditions = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit}

        if receipt_uuid is not None:
            conditions.append("r.receipt_uuid = :receipt_uuid")
            params["receipt_uuid"] = receipt_uuid

        where_clause = " AND ".join(conditions)

        sql = f"""
            WITH ActividadReciente AS (
                SELECT
                    r.receipt_uuid,
                    m.name AS comercio,
                    (
                        SELECT file_key
                        FROM receipt_images
                        WHERE receipt_id = r.id
                        LIMIT 1
                    ) AS file_key,
                    r.created_at  AS fecha_alta,
                    r.total,
                    CASE
                        WHEN re_bi_d.billing_status IS NULL
                          OR re_bi_d.billing_status = 'NOT_REQUESTED'
                        THEN (
                            SELECT status
                            FROM receipt_jobs_details
                            WHERE receipt_id = r.id
                            ORDER BY created_at DESC
                            LIMIT 1
                        )
                        ELSE re_bi_d.billing_status
                    END AS status
                FROM receipts r
                LEFT JOIN merchants m
                       ON r.merchant_id = m.id
                LEFT JOIN receipt_billing_details re_bi_d
                       ON re_bi_d.receipt_id = r.id
                WHERE {where_clause}
            )
            SELECT
                comercio,
                file_key,
                fecha_alta,
                total,
                status
            FROM ActividadReciente
            {"WHERE status = :status_filter" if status_filter is not None else ""}
            ORDER BY fecha_alta DESC
            LIMIT :limit;
        """

        if status_filter is not None:
            params["status_filter"] = status_filter

        return await self._db_manager.execute_sql_query_fetch_all(sql, params)

    async def get_cfdi_list(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> CfdiListResponse:
        offset = (page - 1) * page_size

        where_clause = """
            FROM receipt_billing_details rbd
            INNER JOIN receipts r
                ON r.id = rbd.receipt_id
            WHERE r.user_id = :user_id
              AND rbd.cfdi_summary->'emisor' IS NOT NULL
        """
        count_sql = f"SELECT COUNT(*) AS total {where_clause};"
        count_row = await self._db_manager.execute_sql_query_fetch_first(
            count_sql, {"user_id": user_id}
        )
        total = int(count_row["total"]) if count_row else 0

        # `cfdi_summary` se escribe siempre vía CfdiDto.to_dict() (snake_case).
        sql = f"""
            SELECT
                r.receipt_uuid,
                rbd.cfdi_summary->'emisor'->>'nombre'   AS emisor_nombre,
                (rbd.cfdi_summary->>'total')::numeric  AS total,
                rbd.cfdi_summary->>'serie'             AS serie,
                rbd.cfdi_summary->>'folio'             AS folio,
                rbd.cfdi_summary->'receptor'->>'uso_cfdi' AS uso_cfdi
            {where_clause}
            ORDER BY rbd.cfdi_summary->>'fecha' DESC
            LIMIT :limit OFFSET :offset;
        """
        rows = await self._db_manager.execute_sql_query_fetch_all(
            sql, {"user_id": user_id, "limit": page_size, "offset": offset}
        )

        items = [
            CfdiListItem(
                receipt_uuid=row["receipt_uuid"],
                emisor_nombre=row["emisor_nombre"],
                total=Decimal(str(row["total"])),
                serie=row["serie"],
                folio=row["folio"],
                uso_cfdi=row["uso_cfdi"],
            )
            for row in rows
        ]

        return CfdiListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_cfdi_detail(self, user_id: str, receipt_uuid: str) -> CfdiResponseDto:
        sql = """
            SELECT
                r.receipt_uuid,
                rbd.cfdi_summary,
                (
                    SELECT bf.file_key
                    FROM billing_files bf
                    WHERE bf.receipt_id = r.id
                      AND bf.file_type = 'XML'
                    ORDER BY bf.created_at DESC
                    LIMIT 1
                ) AS xml_key,
                (
                    SELECT bf.file_key
                    FROM billing_files bf
                    WHERE bf.receipt_id = r.id
                      AND bf.file_type = 'PDF'
                    ORDER BY bf.created_at DESC
                    LIMIT 1
                ) AS pdf_key
            FROM receipts r
            INNER JOIN receipt_billing_details rbd
                ON rbd.receipt_id = r.id
            WHERE r.receipt_uuid = :receipt_uuid
              AND r.user_id = :user_id
              AND rbd.cfdi_summary->'emisor' IS NOT NULL;
        """
        result = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_uuid": receipt_uuid, "user_id": user_id}
        )

        if not result:
            raise ValueError("CFDI no encontrado")

        result_parsed = parse_row_to_str(row=result, json_fields={"cfdi_summary"})

        return CfdiResponseDto(
            receipt_uuid=result["receipt_uuid"],
            cfdi=CfdiDto.from_dict(data=result_parsed["cfdi_summary"]),
            invoice=InvoiceFiles(xml_url=result["xml_key"], pdf_url=result["pdf_key"]),
        )
