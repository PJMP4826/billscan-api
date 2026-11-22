from dataclasses import dataclass

from src.shared.errors.base_exception import BaseAppException


@dataclass(frozen=True)
class BillingFailure:
    """Código y mensaje normalizados de un fallo de facturación."""

    code: str
    message: str

    @classmethod
    def from_exception(cls, exc: Exception) -> "BillingFailure":
        if isinstance(exc, BaseAppException):
            return cls(code=exc.error_code, message=exc.get_message())
        return cls(code=BaseAppException.default_error_code, message=str(exc))
