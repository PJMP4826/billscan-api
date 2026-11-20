import pytest

from src.infrastructure.adapters.security.hmac_rfc_fingerprint import (
    HmacRfcFingerprint,
)


def test_fingerprint_is_deterministic_and_normalizes_rfc():
    fingerprint = HmacRfcFingerprint(secret="test-secret")

    first = fingerprint.fingerprint("ACM010101AAA")
    second = fingerprint.fingerprint("  acm010101aaa  ")

    assert first == second
    assert len(first) == 64


def test_fingerprint_changes_with_secret():
    first = HmacRfcFingerprint(secret="secret-a").fingerprint("ACM010101AAA")
    second = HmacRfcFingerprint(secret="secret-b").fingerprint("ACM010101AAA")

    assert first != second


def test_fingerprint_requires_a_secret():
    with pytest.raises(ValueError):
        HmacRfcFingerprint(secret="")
