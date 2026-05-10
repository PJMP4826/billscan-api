from typing import Optional, Dict, Any
from src.shared.errors.base_exception import BaseAppException


class InfrastructureException(BaseAppException):
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "INFRASTRUCTURE_EXCEPTION",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        final_details = {**(details or {})}
        if status_code is not None:
            final_details["status_code"] = status_code
        if response_body is not None:
            final_details["response_body"] = response_body

        super().__init__(
            message,
            error_code=error_code,
            details=final_details,
            **kwargs
        )





class HttpException(InfrastructureException):
    def __init__(
        self,
        message: str,
        *,
        url: str,
        method: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        response_headers: Optional[Dict[str, str]] = None,
        error_code: str = "HTTP_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        final_details = {**(details or {})}
        final_details["url"] = url
        final_details["method"] = method
        if status_code is not None:
            final_details["status_code"] = status_code
        if response_body is not None:
            final_details["response_body"] = response_body
        if response_headers is not None:
            final_details["response_headers"] = response_headers

        super().__init__(
            message,
            error_code=error_code,
            details=final_details,
            **kwargs
        )




class LLMException(InfrastructureException):
    def __init__(
        self,
        message: str,
        *,
        model: Optional[str] = None,
        error_code: str = "LLM_ERROR",
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        final_details = {**(details or {})}
        if model:
            final_details["model"] = model

        super().__init__(
            message,
            error_code=error_code,
            details=final_details,
            **kwargs
        )