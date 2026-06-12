from src.infrastructure.schemas.receipt_data import ReceiptData as ReceiptDataSchema
from src.domain.entities.receipt import Receipt
from src.domain.value_objects.merchant_data import MerchantData
from src.domain.value_objects.transaction_metadata import TransactionMetadata
from src.domain.value_objects.line_item import LineItem
from src.domain.value_objects.tax_detail import TaxDetail
from src.domain.value_objects.totals_and_taxes import TotalsAndTaxes
from src.domain.value_objects.payment_info import PaymentInfo
from src.domain.value_objects.billing_data import BillingData


class ReceiptMapper:
    """Mapea objetos del schema Pydantic (infrastructure) a entidades del dominio."""

    @staticmethod
    def schema_to_domain(
        schema: ReceiptDataSchema,
        receipt_id: str,
    ) -> Receipt:
        merchant = MerchantData(
            name=schema.merchant.name,
            tax_id=schema.merchant.tax_id,
            address=schema.merchant.address,
            branch_id=schema.merchant.branch_id,
            phone=schema.merchant.phone,
        )

        transaction = TransactionMetadata(
            transaction_date=schema.transaction.transaction_date,
            transaction_time=schema.transaction.transaction_time,
            receipt_id=schema.transaction.receipt_id,
            pos_id=schema.transaction.pos_id,
            cashier=schema.transaction.cashier,
        )

        items = [
            LineItem(
                quantity=item.quantity,
                description=item.description,
                sku=item.sku,
                unit_price=item.unit_price,
                total_price=item.total_price,
                discount=item.discount,
                item_metadata=item.item_metadata
            )
            for item in schema.items
        ]

        taxes = [
            TaxDetail(
                name=tax.name,
                rate=tax.rate,
                amount=tax.amount,
            )
            for tax in schema.totals.taxes
        ]

        totals = TotalsAndTaxes(
            subtotal=schema.totals.subtotal,
            total_discount=schema.totals.total_discount,
            taxes=taxes,
            total=schema.totals.total,
            amount_paid=schema.totals.amount_paid,
            change=schema.totals.change
        )

        payment = PaymentInfo(
            method_code=schema.payment.method_code,
            method_description=schema.payment.method_description,
            card_last_four=schema.payment.card_last_four,
            authorization_code=schema.payment.authorization_code,
        )

        billing: BillingData | None = None
        if schema.billing is not None:
            billing = BillingData(
                is_billable=schema.billing.is_billable,
                has_qr_code=schema.billing.has_qr_code,
                billing_url=schema.billing.billing_url,
                billing_code=schema.billing.billing_code,
                barcode=schema.billing.barcode,
                expiration_date=schema.billing.expiration_date,
                billing_metadata=schema.billing.billing_metadata
            )

        return Receipt(
            receipt_id=receipt_id,
            merchant=merchant,
            transaction=transaction,
            items=items,
            totals=totals,
            payment=payment,
            billing=billing,
            context_notes=schema.context_notes,
            extra_metadata=schema.extra_metadata
        )
