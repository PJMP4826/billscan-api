from decimal import Decimal
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.infrastructure.records.deductible_expense_summary import (
    DeductibleExpenseSummary,
)
from src.infrastructure.records.issued_cfdi_summary import IssuedCFDISummary
from src.infrastructure.records.recent_activity_item import RecentActivityItem
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

    async def get_deductible_expenses_summary(self) -> DeductibleExpenseSummary:
        sql = """
            SELECT
                COALESCE(SUM(r.total), 0)  AS total_posibles_gastos_deducibles,
                COUNT(r.id)                AS receipts_por_procesar
            FROM receipts r
            WHERE
                EXISTS (
                    SELECT 1
                    FROM receipt_billing_details re_bi_d
                    WHERE
                        re_bi_d.receipt_id = r.id
                        AND re_bi_d.is_billable  = TRUE
                        AND re_bi_d.billing_status = 'PENDING'
                )
                AND EXISTS (
                    SELECT 1
                    FROM receipt_jobs_details re_job_d
                    WHERE
                        re_job_d.receipt_id = r.id
                        AND re_job_d.status = 'COMPLETED'
                );
        """
        row = await self._db_manager.execute_sql_query_fetch_one(sql, {})

        if not row:
            raise ValueError("Error obteniendo reporte tickets deducibles")

        return DeductibleExpenseSummary(
            total_posibles_gastos_deducibles=Decimal(
                str(row["total_posibles_gastos_deducibles"])
            ),
            receipts_por_procesar=int(row["receipts_por_procesar"]),
        )

    async def get_issued_cfdi_summary(self) -> IssuedCFDISummary:
        sql = """
            SELECT
                COALESCE(SUM(r.total), 0) AS total_facturado,
                COUNT(r.id)               AS facturas_generadas
            FROM receipts r
            WHERE
                EXISTS (
                    SELECT 1
                    FROM billing_files bf
                    WHERE bf.receipt_id = r.id
                )
                AND EXISTS (
                    SELECT 1
                    FROM receipt_jobs_details re_job_d
                    WHERE
                        re_job_d.receipt_id = r.id
                        AND re_job_d.status = 'COMPLETED'
                )
                AND EXISTS (
                    SELECT 1
                    FROM receipt_billing_details re_bi_d
                    WHERE
                        re_bi_d.receipt_id = r.id
                        AND re_bi_d.billing_status = 'COMPLETED'
                );
        """
        row = await self._db_manager.execute_sql_query_fetch_one(sql, {})

        if not row:
            raise ValueError("Error obteniendo reporte de facturas")

        return IssuedCFDISummary(
            total_facturado=Decimal(str(row["total_facturado"])),
            facturas_generadas=int(row["facturas_generadas"]),
        )

    async def get_recent_activity(
        self,
        receipt_uuid: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
    ) -> list[RecentActivityItem]:
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
                        SELECT file_url
                        FROM receipt_images
                        WHERE receipt_id = r.id
                        LIMIT 1
                    ) AS file_url,
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
                file_url,
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

        rows = await self._db_manager.execute_sql_query_fetch_all(sql, params)
        return [
            RecentActivityItem(
                comercio=row["comercio"],
                file_url=row["file_url"],
                fecha_alta=str(row["fecha_alta"]),
                total=Decimal(str(row["total"])),
                status=row["status"],
            )
            for row in rows
        ]

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
                ri.file_url,
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

        result = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"receipt_uuid": receipt_uuid}
        )

        if not result:
            raise ValueError("Ticket no encontrado")

        return parse_row_to_str(row=result)

    async def get_receipt_full_detail(self, receipt_uuid: str) -> dict[str, str | None]:
        sql = """
            SELECT
                r.*,
                m.name                  AS merchant_name,
                m.tax_id                AS merchant_tax_id,
                rbd.billing_status,
                rbd.billing_url,
                rbd.billing_code,
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
            WHERE r.receipt_uuid = :receipt_uuid;
        """
        result = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"receipt_uuid": receipt_uuid}
        )

        if not result:
            raise ValueError("Ticket no encontrado")

        return parse_row_to_str(row=result)
