from typing import Any, Dict, Optional
from fastapi import status


class AppException(Exception):
    """Base exception class for all application exceptions"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(self.message)


class HTTPException(AppException):
    """Exception for HTTP-related errors"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, extra)


class ValidationException(AppException):
    """Exception for data validation errors"""

    def __init__(
        self,
        message: str,
        errors: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            extra={"validation_errors": errors, **(extra or {})},
        )


class ExternalServiceException(AppException):
    """Exception for errors from external service calls"""

    def __init__(
        self, message: str, service_name: str, extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            extra={"service_name": service_name, **(extra or {})},
        )


class RateLimitException(AppException):
    """Exception for rate limiting errors"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, extra=extra
        )


class AuthenticationException(AppException):
    """Exception for authentication errors"""

    def __init__(
        self,
        message: str = "Authentication failed",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, extra=extra)


class AuthorizationException(AppException):
    """Exception for authorization errors"""

    def __init__(
        self, message: str = "Permission denied", extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, extra=extra)


class NotFoundException(AppException):
    """Exception for resource not found errors"""

    def __init__(
        self,
        message: str = "Resource not found",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, extra=extra)
