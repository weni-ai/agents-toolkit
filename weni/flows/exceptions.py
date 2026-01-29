"""
Exceptions for Flows API client.
"""

from typing import Any


class FlowsAPIError(Exception):
    """Base exception for Flows API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class FlowsAuthenticationError(FlowsAPIError):
    """Raised when authentication fails (401/403)."""

    pass


class FlowsNotFoundError(FlowsAPIError):
    """Raised when a resource is not found (404)."""

    pass


class FlowsValidationError(FlowsAPIError):
    """Raised when request validation fails (400)."""

    pass


class FlowsServerError(FlowsAPIError):
    """Raised when server returns 5xx errors."""

    pass


class FlowsConfigurationError(Exception):
    """Raised when the client is misconfigured."""

    pass
