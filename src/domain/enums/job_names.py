from enum import Enum


class JobName(str, Enum):
    PROCESS_RECEIPT_EXTRACTION = "process_receipt_extraction"
    INITIATE_BILLING = "initiate_billing"
