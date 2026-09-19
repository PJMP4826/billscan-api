from decimal import Decimal
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.application.dtos.completed_billing_summary_dto import (
    CompletedBillingSummary,
)
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

    _FULL_DETAIL_JSON_FIELDS = {"items", "taxes", "payments", "extra_metadata"}

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

    async def get_receipt_base_detail(self, receipt_uuid: str) -> dict[str, str | None]:
        sql = """
            SELECT
                r.receipt_uuid,
                m.name                          AS merchant_name,
                m.tax_id                        AS merchant_rfc,
                r.transaction_date              AS fecha_ticket,
                r.subtotal,
                COALESCE(r.total_discount, 0)   AS descuento,
                COALESCE(r.amount_paid,    0)   AS monto_pagado,
                COALESCE(r.change,         0)   AS cambio,
                r.total                         AS total_ticket,
                ri.file_key,
                f_info.use_cfdi_default         AS uso_cfdi,
                r.payment_method_code           AS metodo_pago_codigo,
                pm.description                  AS metodo_pago_descripcion
            FROM receipts r
            LEFT JOIN merchants m
                   ON r.merchant_id       = m.id
            LEFT JOIN receipt_images ri
                   ON ri.receipt_id       = r.id
                  AND ri.page_number      = 1
            LEFT JOIN users u
                   ON r.user_id           = u.id
            LEFT JOIN fiscal_info f_info
                   ON u.id               = f_info.user_id
            LEFT JOIN payment_methods pm
                   ON r.payment_method_code = pm.code
            WHERE r.receipt_uuid = :receipt_uuid;
        """

        result = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_uuid": receipt_uuid}
        )

        if not result:
            raise ValueError("Ticket no encontrado")

        return parse_row_to_str(row=result)

    async def get_receipt_full_detail(self, receipt_uuid: str) -> dict[str, Any | None]:
        sql = """
            SELECT
                r.*,
                m.name                  AS merchant_name,
                m.tax_id                AS merchant_tax_id,
                rbd.billing_status,
                rbd.billing_url,
                rbd.billing_code,
                ri.file_key,
                (
                    SELECT JSON_AGG(items)
                    FROM (
                        SELECT * FROM receipt_items
                        WHERE receipt_id = r.id
                    ) AS items
                ) AS items,
                (
                    SELECT JSON_AGG(taxes)
                    FROM (
                        SELECT * FROM receipt_taxes
                        WHERE receipt_id = r.id
                    ) AS taxes
                ) AS taxes,
                (
                    SELECT JSON_AGG(payments)
                    FROM (
                        SELECT * FROM receipt_payments
                        WHERE receipt_id = r.id
                    ) AS payments
                ) AS payments
            FROM receipts r
            LEFT JOIN merchants m
                   ON r.merchant_id  = m.id
            LEFT JOIN receipt_billing_details rbd
                   ON rbd.receipt_id = r.id
            LEFT JOIN receipt_images ri
                ON ri.receipt_id = r.id
                AND ri.page_number = 1
            WHERE r.receipt_uuid = :receipt_uuid;
        """
        result = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_uuid": receipt_uuid}
        )

        if not result:
            raise ValueError("Ticket no encontrado")

        return parse_row_to_str(row=result, json_fields=self._FULL_DETAIL_JSON_FIELDS)
