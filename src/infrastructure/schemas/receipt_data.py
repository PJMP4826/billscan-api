from pydantic import BaseModel, Field
from typing import List, Optional
from src.infrastructure.schemas.merchant_data import MerchantData
from src.infrastructure.schemas.transaction_metadata import TransactionMetadata
from src.infrastructure.schemas.line_item import LineItem
from src.infrastructure.schemas.totals_and_taxes import TotalsAndTaxes
from src.infrastructure.schemas.payment_info import PaymentInfo
from src.infrastructure.schemas.billing_data import BillingData


class ReceiptData(BaseModel):
    merchant: MerchantData
    transaction: TransactionMetadata
    items: List[LineItem]
    totals: TotalsAndTaxes
    payment: PaymentInfo
    billing: Optional[BillingData] = None
    context_notes: Optional[str] = Field(None, description="Otras notas como políticas de devolución.")
