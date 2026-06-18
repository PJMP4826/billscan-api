from src.infrastructure.database.sql.sql_database_connection_manager import (
    database_connection_manager,
)
from src.infrastructure.repositories.receipt_job_details_repository import (
    ReceiptJobDetailsRepository,
)
from src.infrastructure.repositories.receipt_image_repository import (
    ReceiptImageRepository,
)
from src.infrastructure.repositories.merchant_repository import MerchantRepository
from src.infrastructure.repositories.receipt_repository import ReceiptRepository

from src.infrastructure.repositories.receipt_item_repository import (
    ReceiptItemRepository,
)
from src.infrastructure.repositories.receipt_tax_repository import ReceiptTaxRepository
from src.infrastructure.repositories.receipt_payment_repository import (
    ReceiptPaymentRepository,
)
from src.infrastructure.repositories.receipt_billing_detail_repository import (
    ReceiptBillingDetailRepository,
)


def get_receipt_job_details_repository() -> ReceiptJobDetailsRepository:
    return ReceiptJobDetailsRepository(manager=database_connection_manager)


def get_receipt_image_repository() -> ReceiptImageRepository:
    return ReceiptImageRepository(manager=database_connection_manager)


def get_merchant_repository() -> MerchantRepository:
    return MerchantRepository(manager=database_connection_manager)


def get_receipt_repository() -> ReceiptRepository:
    return ReceiptRepository(manager=database_connection_manager)


def get_receipt_item_repository() -> ReceiptItemRepository:
    return ReceiptItemRepository(manager=database_connection_manager)


def get_receipt_tax_repository() -> ReceiptTaxRepository:
    return ReceiptTaxRepository(manager=database_connection_manager)


def get_receipt_payment_repository() -> ReceiptPaymentRepository:
    return ReceiptPaymentRepository(manager=database_connection_manager)


def get_receipt_billing_detail_repository() -> ReceiptBillingDetailRepository:
    return ReceiptBillingDetailRepository(manager=database_connection_manager)
