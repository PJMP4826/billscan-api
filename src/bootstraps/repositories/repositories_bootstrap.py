from src.infrastructure.database.sql.sql_database_connection_manager import database_connection_manager
from src.infrastructure.repositories.receipt_job_details_repository import ReceiptJobDetailsRepository
from src.infrastructure.repositories.receipt_image_repository import ReceiptImageRepository

def get_receipt_job_details_repository() -> ReceiptJobDetailsRepository:
    return ReceiptJobDetailsRepository(manager=database_connection_manager)

def get_receipt_image_repository() -> ReceiptImageRepository:
    return ReceiptImageRepository(manager=database_connection_manager)