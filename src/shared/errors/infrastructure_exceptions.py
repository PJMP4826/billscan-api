from typing import Any, Dict, Optional

from src.shared.errors.base_exception import BaseAppException


class InfrastructureException(BaseAppException):
    http_status = 500
    default_error_code = "INFRASTRUCTURE_EXCEPTION"
    default_title = "Internal Server Error"
    is_public = False

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        upstream_status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        final_details = {**(details or {})}
        if upstream_status_code is not None:
            final_details["upstream_status_code"] = upstream_status_code
        if response_body is not None:
            final_details["response_body"] = response_body

        super().__init__(
            message, error_code=error_code, details=final_details, **kwargs
        )


class HttpException(InfrastructureException):
    http_status = 502
    default_error_code = "HTTP_ERROR"
    default_title = "Bad Gateway"
    is_public = False

    def __init__(
        self,
        message: str,
        *,
        url: str,
        method: str,
        upstream_status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        response_headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        final_details = {**(details or {})}
        final_details["url"] = url
        final_details["method"] = method
        if upstream_status_code is not None:
            final_details["upstream_status_code"] = upstream_status_code
        if response_body is not None:
            final_details["response_body"] = response_body
        if response_headers is not None:
            final_details["response_headers"] = response_headers

        super().__init__(
            message, error_code=error_code, details=final_details, **kwargs
        )


class LLMException(InfrastructureException):
    http_status = 502
    default_error_code = "LLM_ERROR"
    default_title = "Bad Gateway"
    is_public = False

    def __init__(
        self,
        message: str,
        *,
        model: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        final_details = {**(details or {})}
        if model:
            final_details["model"] = model

        super().__init__(
            message, error_code=error_code, details=final_details, **kwargs
        )


class PostgresDBException(InfrastructureException):
    http_status = 500
    default_error_code = "POSTGRES_DB_ERROR"
    default_title = "Internal Server Error"
    is_public = False

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        final_details = {**(details or {})}

        super().__init__(
            message, error_code=error_code, details=final_details, **kwargs
        )
