from src.domain.errors.billing_error import (
    InvoiceQuotaExceededError,
    build_quota_message,
)


def test_build_quota_message_when_quota_is_exhausted():
    message = build_quota_message(
        limit=3, used=3, requested=1, remaining=0
    )

    assert message == (
        "Ya usaste 3 de 3 facturas gratis de este RFC; "
        "tu solicitud de 1 factura gratis no se procesó."
    )


def test_build_quota_message_when_partial_quota_remains_singular():
    message = build_quota_message(
        limit=3, used=2, requested=2, remaining=1
    )

    assert message == (
        "Tu solicitud de 2 facturas gratis excede el límite: "
        "solo te queda 1 factura gratis en este RFC "
        "(2 de 3 usadas). Reduce el lote a 1."
    )


def test_build_quota_message_when_partial_quota_remains_plural():
    message = build_quota_message(
        limit=5, used=1, requested=5, remaining=4
    )

    assert message == (
        "Tu solicitud de 5 facturas gratis excede el límite: "
        "solo te quedan 4 facturas gratis en este RFC "
        "(1 de 5 usadas). Reduce el lote a 4."
    )


def test_build_quota_message_when_batch_exceeds_limit_without_usage():
    message = build_quota_message(
        limit=3, used=0, requested=5, remaining=3
    )

    assert message == (
        "El máximo es 3 facturas gratis por RFC y solicitaste 5. "
        "Reduce el lote a 3."
    )


def test_build_quota_message_when_limit_is_zero():
    message = build_quota_message(
        limit=0, used=0, requested=1, remaining=0
    )

    assert message == "Este RFC no tiene facturas gratis disponibles."


def test_build_quota_message_uses_custom_quota_label():
    message = build_quota_message(
        limit=3,
        used=3,
        requested=1,
        remaining=0,
        quota_label="de tu plan",
    )

    assert message == (
        "Ya usaste 3 de 3 facturas de tu plan de este RFC; "
        "tu solicitud de 1 factura de tu plan no se procesó."
    )


def test_error_exposes_quota_label_in_details():
    error = InvoiceQuotaExceededError(
        limit=3, used=3, requested=1, quota_label="de tu plan"
    )

    assert error.details == {
        "limit": 3,
        "used": 3,
        "requested": 1,
        "remaining": 0,
        "quota_label": "de tu plan",
    }
