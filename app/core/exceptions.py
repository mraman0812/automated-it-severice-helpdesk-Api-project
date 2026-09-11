from typing import Any, Optional
from fastapi import HTTPException, status


class HelpdeskException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "An error occurred",
        error_code: str = "BAD_REQUEST",
        data: Optional[Any] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_code = error_code
        self.data = data


class NotFoundException(HelpdeskException):
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, error_code=error_code)


class UnauthorizedException(HelpdeskException):
    def __init__(self, message: str = "Could not validate credentials", error_code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code=error_code,
        )


class ForbiddenException(HelpdeskException):
    def __init__(self, message: str = "Permission denied", error_code: str = "FORBIDDEN"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message, error_code=error_code)


class ConflictException(HelpdeskException):
    def __init__(self, message: str = "Resource already exists", error_code: str = "CONFLICT"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, error_code=error_code)


class ValidationException(HelpdeskException):
    def __init__(self, message: str = "Validation failed", error_code: str = "VALIDATION_ERROR"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, error_code=error_code)
