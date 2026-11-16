from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BadRequestError


class InvalidReportingPeriodError(BadRequestError):
    default_error_code = "INVALID_REPORTING_PERIOD"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, error_code=error_code, details=details, **kwargs
        )
