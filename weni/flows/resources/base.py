"""
Base resource class for Flows API resources.

Provides common HTTP request functionality with proper error handling.
"""

from typing import TYPE_CHECKING, Any

import requests
from requests import Response

from weni.flows.exceptions import (
    FlowsAPIError,
    FlowsAuthenticationError,
    FlowsNotFoundError,
    FlowsServerError,
    FlowsValidationError,
)

if TYPE_CHECKING:
    from weni.flows.client import FlowsClient


class BaseResource:
    """
    Base class for all Flows API resources.

    Provides HTTP methods (GET, POST, PATCH, DELETE) with:
    - Automatic JWT authentication
    - Consistent error handling
    - Response parsing
    """

    def __init__(self, client: "FlowsClient"):
        self._client = client

    @property
    def _base_url(self) -> str:
        """Base URL for the Flows API."""
        return self._client.base_url

    @property
    def _headers(self) -> dict[str, str]:
        """Default headers including JWT authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._client.jwt_token:
            headers["Authorization"] = f"Bearer {self._client.jwt_token}"
        return headers

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        base = self._base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _handle_response(self, response: Response) -> dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions on errors.

        Args:
            response: The requests Response object.

        Returns:
            Parsed JSON response data.

        Raises:
            FlowsAuthenticationError: For 401/403 responses.
            FlowsNotFoundError: For 404 responses.
            FlowsValidationError: For 400 responses.
            FlowsServerError: For 5xx responses.
            FlowsAPIError: For other error responses.
        """
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"raw": response.text}

        if response.ok:
            return data

        error_message = data.get("error") or data.get("detail") or data.get("message") or str(data)

        if response.status_code in (401, 403):
            raise FlowsAuthenticationError(
                message=error_message,
                status_code=response.status_code,
                response_data=data,
            )
        elif response.status_code == 404:
            raise FlowsNotFoundError(
                message=error_message,
                status_code=response.status_code,
                response_data=data,
            )
        elif response.status_code == 400:
            raise FlowsValidationError(
                message=error_message,
                status_code=response.status_code,
                response_data=data,
            )
        elif response.status_code >= 500:
            raise FlowsServerError(
                message=error_message,
                status_code=response.status_code,
                response_data=data,
            )
        else:
            raise FlowsAPIError(
                message=error_message,
                status_code=response.status_code,
                response_data=data,
            )

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a GET request.

        Args:
            path: API endpoint path.
            params: Query parameters.
            **kwargs: Additional arguments passed to requests.get().

        Returns:
            Parsed JSON response.
        """
        url = self._build_url(path)
        response = requests.get(
            url,
            headers=self._headers,
            params=params,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        return self._handle_response(response)

    def _post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a POST request.

        Args:
            path: API endpoint path.
            data: Form data to send.
            json_data: JSON data to send.
            **kwargs: Additional arguments passed to requests.post().

        Returns:
            Parsed JSON response.
        """
        url = self._build_url(path)
        response = requests.post(
            url,
            headers=self._headers,
            data=data,
            json=json_data,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        return self._handle_response(response)

    def _patch(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a PATCH request.

        Args:
            path: API endpoint path.
            data: Form data to send.
            json_data: JSON data to send.
            **kwargs: Additional arguments passed to requests.patch().

        Returns:
            Parsed JSON response.
        """
        url = self._build_url(path)
        response = requests.patch(
            url,
            headers=self._headers,
            data=data,
            json=json_data,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        return self._handle_response(response)

    def _delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path.
            **kwargs: Additional arguments passed to requests.delete().

        Returns:
            Parsed JSON response.
        """
        url = self._build_url(path)
        response = requests.delete(
            url,
            headers=self._headers,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        return self._handle_response(response)
