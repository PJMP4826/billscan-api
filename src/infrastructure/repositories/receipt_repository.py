import json
from decimal import Decimal
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from src.domain.entities.receipt import Receipt
from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)
from src.domain.value_objects.billing_data import BillingData
from src.domain.value_objects.line_item import LineItem
from src.domain.value_objects.merchant_data import MerchantData
from src.domain.value_objects.payment_info import PaymentInfo
from src.domain.value_objects.tax_detail import TaxDetail
from src.domain.value_objects.totals_and_taxes import TotalsAndTaxes
from src.domain.value_objects.transaction_metadata import TransactionMetadata
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.domain.errors.receipt_error import ReceiptNotFoundError
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.receipt_repository_port import ReceiptRepositoryPort


class ReceiptRepository(ReceiptRepositoryPort):
    """Repository managing the persistence, retrieval, and life-cycle of the Receipt Aggregate Root."""

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db = manager

    async def save(
        self,
        receipt: Receipt,
        user_id: str | None = None,
        merchant_id: int | None = None,
    ) -> int:
        """Atomically persists the entire Receipt aggregate within a single database transaction.

        If any child insertion fails, the entire transaction is rolled back.
        """
        async with self._db.transaction() as conn:
            # 1. Insert Receipt Header
            receipt_id = await self._insert_header(conn, receipt, user_id, merchant_id)

            # 2. Batch Insert Items
            if receipt.items:
                await self._insert_items(conn, receipt_id, receipt.items)

            # 3. Batch Insert Taxes
            if receipt.totals.taxes:
                await self._insert_taxes(conn, receipt_id, receipt.totals.taxes)

            # 4. Insert Billing Details (1:1 with defaults if None)
            await self._insert_billing(conn, receipt_id, receipt.billing)

            return receipt_id

    async def find_by_id(self, receipt_id: int) -> Receipt:
        return await self._find_single(
            where_clause="r.id = :id", params={"id": receipt_id}
        )

    async def find_by_uuid(self, user_id: str, receipt_uuid: str) -> Receipt:
        return await self._find_single(
            where_clause="r.receipt_uuid = :uuid AND r.user_id = :user_id",
            params={"uuid": receipt_uuid, "user_id": user_id},
        )

    async def find_id_by_uuid(self, receipt_uuid: str) -> int | None:
        """Resuelve el id (BIGSERIAL) a partir del UUID público (external_id
        que FacturaGPT devuelve en los webhooks)."""
        sql = """
            SELECT id
            FROM receipts
            WHERE receipt_uuid = :uuid;
        """
        row = await self._db.execute_sql_query_fetch_first(sql, {"uuid": receipt_uuid})
        return int(row["id"]) if row else None

    async def find_user_id_by_receipt_id(self, receipt_id: int) -> str | None:
        """Devuelve el `user_id` dueño del receipt (NULL en receipts sin usuario)."""
        sql = """
            SELECT user_id
            FROM receipts
            WHERE id = :id;
        """
        row = await self._db.execute_sql_query_fetch_first(sql, {"id": receipt_id})
        if not row:
            return None
        user_id = row["user_id"]
        return str(user_id) if user_id is not None else None

    async def delete(self, receipt_id: int) -> None:
        """Deletes a receipt and relies on ON DELETE CASCADE for aggregate children."""
        async with self._db.transaction() as conn:
            await conn.execute(
                text("DELETE FROM receipts WHERE id = :id;"), {"id": receipt_id}
            )

    # -------------------------------------------------------------------------
    # Private Atomic Persistence Helpers
    # -------------------------------------------------------------------------

    async def _insert_header(
        self,
        conn: AsyncConnection,
        receipt: Receipt,
        user_id: str | None,
        merchant_id: int | None,
    ) -> int:
        query = text("""
            INSERT INTO receipts (
                user_id, merchant_id, payment_method_code,
                transaction_date, transaction_time, ticket_number, pos_id, cashier,
                subtotal, total_discount, total, amount_paid, "change",
                card_last_four, authorization_code, context_notes,
                receipt_uuid, extra_metadata
            ) VALUES (
                :user_id, :merchant_id, :payment_method_code,
                :transaction_date, :transaction_time, :ticket_number, :pos_id, :cashier,
                :subtotal, :total_discount, :total, :amount_paid, :change,
                :card_last_four, :authorization_code, :context_notes,
                :receipt_uuid, :extra_metadata
            )
            RETURNING id;
        """)
        params: dict[str, Any] = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "payment_method_code": (
                receipt.payment.method_code.value
                if receipt.payment.method_code
                else None
            ),
            "transaction_date": receipt.transaction.transaction_date,
            "transaction_time": receipt.transaction.transaction_time,
            "ticket_number": receipt.transaction.ticket_number,
            "pos_id": receipt.transaction.pos_id,
            "cashier": receipt.transaction.cashier,
            "subtotal": receipt.totals.subtotal,
            "total_discount": receipt.totals.total_discount,
            "total": receipt.totals.total,
            "amount_paid": receipt.totals.amount_paid,
            "change": receipt.totals.change,
            "card_last_four": receipt.payment.card_last_four,
            "authorization_code": receipt.payment.authorization_code,
            "context_notes": receipt.context_notes,
            "receipt_uuid": receipt.receipt_uuid,
            "extra_metadata": (
                json.dumps(receipt.extra_metadata) if receipt.extra_metadata else None
            ),
        }
        res = await conn.execute(query, params)
        receipt_id = res.scalar_one_or_none()
        if not receipt_id:
            raise PostgresDBException("Failed to persist receipt header.")
        return int(receipt_id)

    async def _insert_items(
        self, conn: AsyncConnection, receipt_id: int, items: list[LineItem]
    ) -> None:
        query = text("""
            INSERT INTO receipt_items (
                receipt_id, quantity, description, sku,
                unit_price, total_price, discount, item_metadata
            ) VALUES (
                :receipt_id, :quantity, :description, :sku,
                :unit_price, :total_price, :discount, :item_metadata
            );
        """)
        params: list[dict[str, Any]] = [
            {
                "receipt_id": receipt_id,
                "quantity": item.quantity,
                "description": item.description,
                "sku": item.sku,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "discount": item.discount,
                "item_metadata": (
                    json.dumps(item.item_metadata) if item.item_metadata else None
                ),
            }
            for item in items
        ]
        await conn.execute(query, params)

    async def _insert_taxes(
        self, conn: AsyncConnection, receipt_id: int, taxes: list[TaxDetail]
    ) -> None:
        query = text("""
            INSERT INTO receipt_taxes (receipt_id, tax_name, tax_rate, amount)
            VALUES (:receipt_id, :tax_name, :tax_rate, :amount);
        """)
        params: list[dict[str, Any]] = [
            {
                "receipt_id": receipt_id,
                "tax_name": tax.name,
                "tax_rate": tax.rate,
                "amount": tax.amount,
            }
            for tax in taxes
        ]
        await conn.execute(query, params)

    async def _insert_billing(
        self, conn: AsyncConnection, receipt_id: int, billing: BillingData | None
    ) -> None:
        query = text("""
            INSERT INTO receipt_billing_details (
                receipt_id, is_billable, has_qr_code, billing_url,
                barcode, billing_code, expiration_date, billing_metadata
            ) VALUES (
                :receipt_id, :is_billable, :has_qr_code, :billing_url,
                :barcode, :billing_code, :expiration_date, :billing_metadata
            );
        """)
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "is_billable": billing.is_billable if billing else False,
            "has_qr_code": billing.has_qr_code if billing else False,
            "billing_url": billing.billing_url if billing else None,
            "barcode": billing.barcode if billing else None,
            "billing_code": billing.billing_code if billing else None,
            "expiration_date": billing.expiration_date if billing else None,
            "billing_metadata": (
                json.dumps(billing.billing_metadata)
                if billing and billing.billing_metadata is not None
                else None
            ),
        }
        await conn.execute(query, params)

    # -------------------------------------------------------------------------
    # Private Entity Reconstruction Helpers
    # -------------------------------------------------------------------------

    async def _find_single(self, where_clause: str, params: dict[str, Any]) -> Receipt:
        """Hydrates the full Receipt aggregate using a single optimized query with JSON aggregations."""
        sql = f"""
            SELECT 
                r.id, r.receipt_uuid, r.user_id, r.merchant_id,
                r.payment_method_code, r.card_last_four, r.authorization_code,
                r.transaction_date, r.transaction_time, r.ticket_number, r.pos_id, r.cashier,
                r.subtotal, r.total_discount, r.total, r.amount_paid, r.change,
                r.context_notes, r.extra_metadata,
                m.name AS merchant_name, m.tax_id AS merchant_tax_id,
                m.address AS merchant_address, m.branch_id AS merchant_branch_id,
                m.phone AS merchant_phone,
                -- Subquery for Items
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(items_sub))
                    FROM (
                        SELECT quantity, description, sku, unit_price, total_price, discount, item_metadata
                        FROM receipt_items
                        WHERE receipt_id = r.id
                        ORDER BY id ASC
                    ) items_sub
                ), '[]'::jsonb) AS items_json,
                -- Subquery for Taxes
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(taxes_sub))
                    FROM (
                        SELECT tax_name, tax_rate, amount
                        FROM receipt_taxes
                        WHERE receipt_id = r.id
                        ORDER BY id ASC
                    ) taxes_sub
                ), '[]'::jsonb) AS taxes_json,
                -- Subquery for Billing Details
                (
                    SELECT to_jsonb(b_sub)
                    FROM (
                        SELECT is_billable, has_qr_code, billing_url, barcode, billing_code, expiration_date, billing_metadata
                        FROM receipt_billing_details
                        WHERE receipt_id = r.id
                    ) b_sub
                ) AS billing_json
            FROM receipts r
            LEFT JOIN merchants m ON r.merchant_id = m.id
            WHERE {where_clause};
        """
        async with self._db.engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            row = result.mappings().first()
            if not row:
                raise ReceiptNotFoundError()

            return self._map_row_to_entity(row)

    async def _load_items(
        self, conn: AsyncConnection, receipt_id: int
    ) -> list[LineItem]:
        query = text("""
            SELECT quantity, description, sku, unit_price, total_price, discount, item_metadata
            FROM receipt_items
            WHERE receipt_id = :receipt_id
            ORDER BY id ASC;
        """)
        result = await conn.execute(query, {"receipt_id": receipt_id})
        items: list[LineItem] = []
        for row in result.mappings().all():
            metadata = row["item_metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            items.append(
                LineItem(
                    quantity=float(row["quantity"]),
                    description=row["description"],
                    sku=row["sku"],
                    unit_price=(
                        Decimal(str(row["unit_price"]))
                        if row["unit_price"] is not None
                        else None
                    ),
                    total_price=Decimal(str(row["total_price"])),
                    discount=(
                        Decimal(str(row["discount"]))
                        if row["discount"] is not None
                        else Decimal("0.00")
                    ),
                    item_metadata=metadata,
                )
            )
        return items

    async def _load_taxes(
        self, conn: AsyncConnection, receipt_id: int
    ) -> list[TaxDetail]:
        query = text("""
            SELECT tax_name, tax_rate, amount
            FROM receipt_taxes
            WHERE receipt_id = :receipt_id
            ORDER BY id ASC;
        """)
        result = await conn.execute(query, {"receipt_id": receipt_id})
        return [
            TaxDetail(
                name=row["tax_name"],
                rate=(
                    Decimal(str(row["tax_rate"]))
                    if row["tax_rate"] is not None
                    else None
                ),
                amount=Decimal(str(row["amount"])),
            )
            for row in result.mappings().all()
        ]

    async def _load_billing(
        self, conn: AsyncConnection, receipt_id: int
    ) -> BillingData | None:
        query = text("""
            SELECT is_billable, has_qr_code, billing_url, barcode, billing_code, expiration_date, billing_metadata
            FROM receipt_billing_details
            WHERE receipt_id = :receipt_id;
        """)
        result = await conn.execute(query, {"receipt_id": receipt_id})
        row = result.mappings().first()
        if not row:
            return None

        metadata = row["billing_metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return BillingData(
            is_billable=row["is_billable"],
            has_qr_code=row["has_qr_code"],
            billing_url=row["billing_url"],
            barcode=row["barcode"],
            billing_code=row["billing_code"],
            expiration_date=row["expiration_date"],
            billing_metadata=metadata,
        )

    def _map_row_to_entity(self, row: Any) -> Receipt:
        merchant = MerchantData(
            name=row["merchant_name"] or "Unknown Merchant",
            tax_id=row["merchant_tax_id"],
            address=row["merchant_address"],
            branch_id=row["merchant_branch_id"],
            phone=row["merchant_phone"],
        )

        transaction = TransactionMetadata(
            transaction_date=row["transaction_date"],
            transaction_time=row["transaction_time"],
            ticket_number=row["ticket_number"],
            pos_id=row["pos_id"],
            cashier=row["cashier"],
        )

        # Parse Aggregated Taxes
        raw_taxes = row["taxes_json"]
        if isinstance(raw_taxes, str):
            raw_taxes = json.loads(raw_taxes)

        taxes = [
            TaxDetail(
                name=t["tax_name"],
                rate=(
                    Decimal(str(t["tax_rate"]))
                    if t.get("tax_rate") is not None
                    else None
                ),
                amount=Decimal(str(t["amount"])),
            )
            for t in raw_taxes
        ]

        totals = TotalsAndTaxes(
            subtotal=(
                Decimal(str(row["subtotal"])) if row["subtotal"] is not None else None
            ),
            total_discount=(
                Decimal(str(row["total_discount"]))
                if row["total_discount"] is not None
                else Decimal("0.00")
            ),
            taxes=taxes,
            total=Decimal(str(row["total"])),
            amount_paid=Decimal(str(row["amount_paid"])),
            change=Decimal(str(row["change"])) if row["change"] is not None else None,
        )

        # Parse Aggregated Items
        raw_items = row["items_json"]
        if isinstance(raw_items, str):
            raw_items = json.loads(raw_items)

        items: list[LineItem] = []
        for i in raw_items:
            metadata = i.get("item_metadata")
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            items.append(
                LineItem(
                    quantity=float(i["quantity"]),
                    description=i["description"],
                    sku=i.get("sku"),
                    unit_price=(
                        Decimal(str(i["unit_price"]))
                        if i.get("unit_price") is not None
                        else None
                    ),
                    total_price=Decimal(str(i["total_price"])),
                    discount=(
                        Decimal(str(i["discount"]))
                        if i.get("discount") is not None
                        else Decimal("0.00")
                    ),
                    item_metadata=metadata,
                )
            )

        # Parse Billing Data
        billing: BillingData | None = None
        raw_billing = row["billing_json"]
        if raw_billing:
            if isinstance(raw_billing, str):
                raw_billing = json.loads(raw_billing)
            b_meta = raw_billing.get("billing_metadata")
            if isinstance(b_meta, str):
                b_meta = json.loads(b_meta)

            billing = BillingData(
                is_billable=raw_billing.get("is_billable", False),
                has_qr_code=raw_billing.get("has_qr_code", False),
                billing_url=raw_billing.get("billing_url"),
                barcode=raw_billing.get("barcode"),
                billing_code=raw_billing.get("billing_code"),
                expiration_date=raw_billing.get("expiration_date"),
                billing_metadata=b_meta,
            )

        # Safe Payment Extraction
        payment_code_raw = row["payment_method_code"]
        payment_code: SatPaymentMethodCode | None = None
        payment_desc: SatPaymentMethodDescription | None = None

        if payment_code_raw:
            payment_code = SatPaymentMethodCode(payment_code_raw)
            payment_desc = SatPaymentMethodDescription[payment_code.name]

        payment = PaymentInfo(
            method_code=payment_code,
            method_description=payment_desc,
            card_last_four=row["card_last_four"],
            authorization_code=row["authorization_code"],
        )

        extra_meta = row["extra_metadata"]
        if isinstance(extra_meta, str):
            extra_meta = json.loads(extra_meta)

        return Receipt(
            receipt_uuid=row["receipt_uuid"],
            merchant=merchant,
            transaction=transaction,
            items=items,
            totals=totals,
            payment=payment,
            billing=billing,
            context_notes=row["context_notes"],
            extra_metadata=extra_meta,
        )
