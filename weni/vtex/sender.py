"""
VTEX proxy sender.

Validates method and path, builds the Retail proxy payload, and posts it
through :class:`RetailClient`.
"""

from typing import Any

from weni.context import Context
from weni.vtex.client import RetailClient
from weni.vtex.exceptions import VtexResponseError, VtexValidationError

JSONObjectOrArray = dict[str, Any] | list[Any]


class VtexSender:
	"""
	Sends generic VTEX proxy requests to Retail during tool execution.

	Configuration is resolved by RetailClient from the execution context.
	This sender owns VTEX-proxy semantics (allowed methods, path shape, payload).
	"""

	PROXY_PATH = '/vtex/proxy/'
	ALLOWED_METHODS = frozenset({'GET', 'POST', 'PUT', 'PATCH'})

	def __init__(self, context: Context):
		self.context = context
		self._client = RetailClient(context)

	@staticmethod
	def normalize_path(path: str) -> str:
		"""
		Normalize a VTEX API path and reject empty or absolute values.

		Args:
			path: The VTEX path supplied by the caller.

		Returns:
			The path with a single leading slash.

		Raises:
			VtexValidationError: If the path is empty or an absolute URL.
		"""
		stripped = path.strip()
		if not stripped:
			raise VtexValidationError('VTEX path must not be empty.')

		lowered = stripped.lower()
		if lowered.startswith('http://') or lowered.startswith('https://'):
			raise VtexValidationError('VTEX path must be a relative API path, not an absolute URL.')

		return f'/{stripped.lstrip("/")}'

	def request(
		self,
		path: str,
		method: str = 'GET',
		headers: dict[str, Any] | None = None,
		data: dict[str, Any] | list[Any] | None = None,
		params: dict[str, Any] | None = None,
		merchant_name: str | None = None,
	) -> JSONObjectOrArray:
		"""
		Forward a VTEX API call through Retail's generic proxy.

		Args:
			path: VTEX API path (leading slash optional).
			method: HTTP method. Allowed: GET, POST, PUT, PATCH.
			headers: Optional headers forwarded to VTEX (not used for Retail auth).
			data: Optional JSON body for POST, PUT, or PATCH.
			params: Optional query parameters appended to the VTEX URL.
			merchant_name: Optional seller account override resolved by Retail.

		Returns:
			The parsed JSON object or array returned by the proxy.

		Raises:
			VtexValidationError: If method or path is invalid.
			VtexConfigError: If Retail URL or auth token is missing (at construction).
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response is empty or not a JSON object/array.
		"""
		verb = method.upper()
		if verb not in self.ALLOWED_METHODS:
			raise VtexValidationError(f'Unsupported method {verb!r}. Allowed: GET, POST, PUT, PATCH.')

		normalized = self.normalize_path(path)
		body: dict[str, Any] = {'method': verb, 'path': normalized}
		if headers:
			body['headers'] = headers
		if data is not None:
			body['data'] = data
		if params:
			body['params'] = params
		if merchant_name:
			body['merchant_name'] = merchant_name

		response = self._client.post(self.PROXY_PATH, json=body)
		if not isinstance(response, (dict, list)):
			raise VtexResponseError('Retail VTEX proxy returned a response that is not a JSON object or array.')

		return response
