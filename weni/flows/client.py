"""
Endpoint-agnostic HTTP client for the Flows platform.

The client resolves its configuration from the execution Context, builds
authenticated requests to arbitrary Flows paths, and translates failures
into the typed error hierarchy from :mod:`weni.flows.exceptions`.
"""

import os
from typing import Any

import requests

from weni.context import Context
from weni.flows.exceptions import (
	FlowsClientConfigError,
	FlowsHTTPError,
	FlowsNetworkError,
	FlowsResponseError,
)

JSONResponse = dict[str, Any] | list[Any] | None


class FlowsClient:
	"""
	Reusable client for authenticated requests to the Flows platform.

	Configuration is resolved eagerly at construction with precedence
	``context.project`` > ``context.credentials`` > ``context.globals`` >
	environment variable, with a default base URL fallback. Requests are
	issued with ``Content-Type: application/json`` and a Bearer token.

	Args:
		context: The execution context of the current tool.

	Raises:
		FlowsClientConfigError: If the auth token cannot be resolved.
	"""

	DEFAULT_FLOWS_URL = 'https://flows.stg.cloud.weni.ai'

	def __init__(self, context: Context):
		self.context = context

		base_url = self._resolve_config('flows_url', 'FLOWS_BASE_URL') or self.DEFAULT_FLOWS_URL
		self.base_url = base_url.rstrip('/')

		auth_token = context.project.get('auth_token')
		if not auth_token:
			raise FlowsClientConfigError("Missing required configuration: 'auth_token' not found in context.project.")
		self.auth_token: str = auth_token

		self.project_uuid: str | None = self._resolve_config('uuid', 'PROJECT_UUID')

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

	def _request(
		self,
		method: str,
		path: str,
		json: dict[str, Any] | None = None,
		params: dict[str, Any] | None = None,
	) -> JSONResponse:
		"""
		Execute an HTTP request against the Flows API.

		Args:
			method: HTTP method (GET, POST, PUT, PATCH, DELETE).
			path: Endpoint path relative to the base URL.
			json: Optional JSON body.
			params: Optional query string parameters.

		Returns:
			The parsed JSON response, or None when the response body is empty.

		Raises:
			FlowsHTTPError: If Flows responds with a non-success status.
			FlowsNetworkError: If the request fails before a response is received.
			FlowsResponseError: If a success response carries an unreadable body.
		"""
		url = self._build_url(path)
		headers = self._build_headers()

		try:
			response = requests.request(method, url, headers=headers, json=json, params=params)
		except requests.exceptions.RequestException as e:
			raise FlowsNetworkError(f'Failed to request Flows: {e}') from e

		try:
			response.raise_for_status()
		except requests.exceptions.HTTPError as e:
			raise FlowsHTTPError(response.status_code, response.text) from e

		if not response.content:
			return None

		try:
			return response.json()
		except ValueError as e:
			raise FlowsResponseError('Flows returned a response body that could not be parsed as JSON.') from e

	def get(self, path: str, params: dict[str, Any] | None = None) -> JSONResponse:
		"""Issue a GET request to the given Flows path."""
		return self._request('GET', path, params=params)

	def post(
		self, path: str, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None
	) -> JSONResponse:
		"""Issue a POST request to the given Flows path."""
		return self._request('POST', path, json=json, params=params)

	def put(self, path: str, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> JSONResponse:
		"""Issue a PUT request to the given Flows path."""
		return self._request('PUT', path, json=json, params=params)

	def patch(
		self, path: str, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None
	) -> JSONResponse:
		"""Issue a PATCH request to the given Flows path."""
		return self._request('PATCH', path, json=json, params=params)

	def delete(self, path: str, params: dict[str, Any] | None = None) -> JSONResponse:
		"""Issue a DELETE request to the given Flows path."""
		return self._request('DELETE', path, params=params)
