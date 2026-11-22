from src.domain.errors.receipt_error import ReceiptNotFoundError
from src.domain.value_objects.billing_failure import BillingFailure
from src.shared.errors.base_exception import BaseAppException


def test_builds_failure_from_domain_exception():
    failure = BillingFailure.from_exception(ReceiptNotFoundError())

    assert failure.code == "RECEIPT_NOT_FOUND"
    assert failure.message == "Ticket no encontrado"


def test_builds_failure_from_generic_exception_using_default_code():
    failure = BillingFailure.from_exception(RuntimeError("boom"))

    assert failure.code == BaseAppException.default_error_code
    assert failure.message == "boom"
