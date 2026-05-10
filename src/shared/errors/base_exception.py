from typing import Optional, Dict, Any


from typing import Optional, Dict, Any
from copy import deepcopy


class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)

        self.error_code: str = error_code

        self.details: Dict[str, Any] = deepcopy(details) if details else {}

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.args[0]}"

    def get_message(self) -> str:
        return self.args[0] if self.args else "Sin error encontrado"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.args[0],
            "error_code": self.error_code,
            "details": deepcopy(self.details),
            "type": self.__class__.__name__,
        }


class NotFoundError(BaseAppException):
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "NOT_FOUND_EXCEPTION",
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details or {}, **kwargs
        )
