"""Custom exception classes and error handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ApplicationException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(ApplicationException):
    """Resource not found exception."""

    def __init__(self, resource: str) -> None:
        """Initialize the exception.

        Args:
            resource: Resource name that was not found
        """
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationException(ApplicationException):
    """Validation error exception."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Validation error message
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ApplicationException)
    async def application_exception_handler(
        request: Request, exc: ApplicationException
    ) -> JSONResponse:
        """Handle application exceptions.

        Args:
            request: Request object
            exc: Exception instance

        Returns:
            JSON response with error details
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions.

        Args:
            request: Request object
            exc: Exception instance

        Returns:
            JSON response with generic error message
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        )
