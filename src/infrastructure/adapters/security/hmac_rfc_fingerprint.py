import hashlib
import hmac

from src.domain.ports.rfc_fingerprint_port import RfcFingerprintPort


class HmacRfcFingerprint(RfcFingerprintPort):
    """Fingerprint HMAC-SHA256 del RFC normalizado.

    Se usa HMAC (y no un hash simple) para que el RFC no pueda recuperarse por
    fuerza bruta a partir del valor almacenado. La normalización
    (``strip`` + mayúsculas) garantiza que ``ACM010101AAA`` y
    `` acm010101aaa `` produzcan el mismo valor.
    """

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("El secreto del fingerprint del RFC no puede estar vacío")
        self._secret = secret.encode("utf-8")

    def fingerprint(self, rfc: str) -> str:
        normalized = rfc.strip().upper()
        return hmac.new(
            self._secret,
            normalized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
