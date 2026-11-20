from src.infrastructure.database.sql.sql_database_connection_manager import (
    database_connection_manager,
)


def get_receipt_job_details_repository():
    from src.infrastructure.repositories.receipt_job_details_repository import (
        ReceiptJobDetailsRepository,
    )

    return ReceiptJobDetailsRepository(manager=database_connection_manager)


def get_receipt_image_repository():
    from src.infrastructure.repositories.receipt_image_repository import (
        ReceiptImageRepository,
    )

    return ReceiptImageRepository(manager=database_connection_manager)


def get_merchant_repository():
    from src.infrastructure.repositories.merchant_repository import MerchantRepository

    return MerchantRepository(manager=database_connection_manager)


def get_receipt_repository():
    from src.infrastructure.repositories.receipt_repository import ReceiptRepository

    return ReceiptRepository(manager=database_connection_manager)


def get_receipt_billing_detail_repository():
    from src.infrastructure.repositories.receipt_billing_detail_repository import (
        ReceiptBillingDetailRepository,
    )

    return ReceiptBillingDetailRepository(manager=database_connection_manager)


def get_fiscal_info_repository():
    from src.infrastructure.repositories.fiscal_info_repository import (
        FiscalInfoRepository,
    )

    return FiscalInfoRepository(manager=database_connection_manager)


def get_reporting_repository():
    from src.infrastructure.repositories.reporting_repository import (
        PostgresReportingRepository,
    )

    return PostgresReportingRepository(manager=database_connection_manager)


def get_facturagpt_webhook_repository():
    from src.infrastructure.repositories.facturagpt_webhook_repository import (
        FacturaGPTWebhookRepository,
    )

    return FacturaGPTWebhookRepository(manager=database_connection_manager)


def get_billing_file_repository():
    from src.infrastructure.repositories.billing_file_repository import (
        BillingFileRepository,
    )

    return BillingFileRepository(manager=database_connection_manager)

def get_user_repository():
    from src.infrastructure.repositories.user_repository import UserRepository

    return UserRepository(manager=database_connection_manager)


def get_invoice_quota_repository():
    from src.infrastructure.repositories.invoice_quota_repository import (
        InvoiceQuotaRepository,
    )

    return InvoiceQuotaRepository(manager=database_connection_manager)
