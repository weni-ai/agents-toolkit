"""
HTTP client for the Retail platform, used by the VTEX proxy integration.

The client resolves its configuration from the execution Context, posts
authenticated JSON to Retail paths, and translates failures into the typed
error hierarchy from :mod:`weni.vtex.exceptions`.
"""

import os
from typing import Any

import requests

from weni.context import Context
from weni.vtex.exceptions import (
	VtexConfigError,
	VtexHTTPError,
	VtexNetworkError,
	VtexResponseError,
)

JSONResponse = dict[str, Any] | list[Any] | None


class RetailClient:
	"""
	Reusable client for authenticated requests to Retail.

	Configuration is resolved eagerly at construction with precedence
	``context.project`` > ``context.credentials`` > ``context.globals`` >
	environment variable, with a default base URL fallback. Requests are
	issued with ``Content-Type: application/json`` and a Bearer token.

	Args:
		context: The execution context of the current tool.

	Raises:
		VtexConfigError: If the auth token cannot be resolved.
	"""

	DEFAULT_RETAIL_URL = 'https://retailsetup.stg.cloud.weni.ai'

	def __init__(self, context: Context):
		self.context = context

		auth_token = context.project.get('auth_token')
		if not auth_token:
			raise VtexConfigError("Missing required configuration: 'auth_token' not found in context.project.")
		self.auth_token: str = auth_token

		base_url = self._resolve_config('retail_url', 'RETAIL_BASE_URL') or self.DEFAULT_RETAIL_URL
		self.base_url = base_url.rstrip('/')

	def _resolve_config(self, key: str, env_var: str) -> str | None:
		"""
		Resolve a configuration value from the context or the environment.

		Priority: context.project > context.credentials > context.globals > environment.
		"""
		return (
			self.context.project.get(key)
			or self.context.credentials.get(key)
			or self.context.globals.get(key)
			or os.environ.get(env_var)
		)

	def _build_url(self, path: str) -> str:
		"""Join the normalized base URL with an endpoint path."""
		return f'{self.base_url}/{path.lstrip("/")}'

	def _build_headers(self) -> dict[str, str]:
		"""Build the headers sent with every request."""
		return {
			'Content-Type': 'application/json',
			'Authorization': f'Bearer {self.auth_token}',
		}

	def _send(self, method: str, url: str, json: dict[str, Any] | None) -> requests.Response:
		"""
		Issue the HTTP request, translating transport failures.

		Raises:
			VtexNetworkError: If the request fails before a response is received.
		"""
		try:
			return requests.request(method, url, headers=self._build_headers(), json=json)
		except requests.exceptions.RequestException as e:
			raise VtexNetworkError(f'Failed to request Retail: {e}') from e

	def _check_status(self, response: requests.Response) -> None:
		"""
		Validate the response status, translating non-success statuses.

		Raises:
			VtexHTTPError: If Retail responded with a non-success status.
		"""
		try:
			response.raise_for_status()
		except requests.exceptions.HTTPError as e:
			raise VtexHTTPError(response.status_code, response.text) from e

	def _parse_response(self, response: requests.Response) -> JSONResponse:
		"""
		Parse a success response body, translating unreadable bodies.

		Returns:
			The parsed JSON body, or None when the body is empty.

		Raises:
			VtexResponseError: If a non-empty body cannot be parsed as JSON.
		"""
		if not response.content:
			return None

		try:
			return response.json()
		except ValueError as e:
			raise VtexResponseError('Retail returned a response body that could not be parsed as JSON.') from e

	def post(self, path: str, json: dict[str, Any] | None = None) -> JSONResponse:
		"""
		Issue a POST request to the given Retail path.

		Args:
			path: Endpoint path relative to the Retail base URL.
			json: Optional JSON body.

		Returns:
			The parsed JSON response, or None when the response body is empty.

		Raises:
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response carries an unreadable body.
		"""
		url = self._build_url(path)
		response = self._send('POST', url, json)
		self._check_status(response)
		return self._parse_response(response)
