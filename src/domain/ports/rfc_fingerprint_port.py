from abc import ABC, abstractmethod


class RfcFingerprintPort(ABC):
    """Genera un fingerprint determinístico del RFC.

    El RFC se guarda cifrado (Fernet usa IV aleatorio), por lo que no se puede
    consultar por igualdad. El fingerprint permite agrupar cuentas que
    comparten el mismo RFC sin almacenarlo en claro.
    """

    @abstractmethod
    def fingerprint(self, rfc: str) -> str:
        """Devuelve el fingerprint del RFC normalizado."""
        pass
