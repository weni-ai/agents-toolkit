"""
VTEX proxy sender.

Validates method and path, builds the Retail proxy payload, and posts it
through :class:`RetailClient`. Order helpers either reuse that proxy or post
the dedicated orders-search body to Retail.
"""

import re
from typing import Any
from urllib.parse import quote

from weni.context import Context
from weni.vtex.client import RetailClient
from weni.vtex.exceptions import VtexResponseError, VtexValidationError

JSONObjectOrArray = dict[str, Any] | list[Any]

_UNSAFE_ORDER_ID = re.compile(r'[/\\?#\s]')


class VtexSender:
	"""
	Sends generic VTEX proxy requests to Retail during tool execution.

	Configuration is resolved by RetailClient from the execution context.
	This sender owns VTEX-proxy semantics (allowed methods, path shape, payload)
	and the fixed order lookups and search.
	"""

	PROXY_PATH = '/vtex/proxy/'
	OMS_ORDER_PATH = '/api/oms/pvt/orders/{order_id}'
	ORDER_DOCUMENT_PATH = '/api/orders/pvt/document/{order_id}'
	ORDERS_SEARCH_PATH = '/vtex/orders/'
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

	@staticmethod
	def order_path(template: str, order_id: str) -> str:
		"""
		Build a VTEX order path from a fixed template and an order id.

		Args:
			template: Path template containing ``{order_id}``.
			order_id: VTEX order identifier.

		Returns:
			The template with the order id quoted and interpolated.

		Raises:
			VtexValidationError: If the order id is empty or contains path,
				query, or whitespace characters.
		"""
		stripped = order_id.strip()
		if not stripped:
			raise VtexValidationError('order_id must not be empty.')
		if _UNSAFE_ORDER_ID.search(stripped):
			raise VtexValidationError('order_id must not contain path separators, query characters, or whitespace.')
		return template.format(order_id=quote(stripped, safe=''))

	@staticmethod
	def normalize_raw_query(raw_query: str) -> str:
		"""
		Normalize an orders-search query string.

		Args:
			raw_query: Query string forwarded to Retail as ``raw_query``.

		Returns:
			The stripped query, prefixed with ``?`` when missing.

		Raises:
			VtexValidationError: If the query is empty.
		"""
		stripped = raw_query.strip()
		if not stripped:
			raise VtexValidationError('raw_query must not be empty.')
		if stripped.startswith('?'):
			return stripped
		return f'?{stripped}'

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

	def get_order(self, order_id: str, merchant_name: str | None = None) -> JSONObjectOrArray:
		"""
		Fetch one OMS order by id through the generic VTEX proxy.

		Args:
			order_id: VTEX order identifier.
			merchant_name: Optional seller account override resolved by Retail.

		Returns:
			The parsed JSON object or array returned by the proxy.

		Raises:
			VtexValidationError: If the order id is invalid.
			VtexConfigError: If Retail URL or auth token is missing (at construction).
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response is empty or not a JSON object/array.
		"""
		path = self.order_path(self.OMS_ORDER_PATH, order_id)
		return self.request(path=path, method='GET', merchant_name=merchant_name)

	def get_order_document(self, order_id: str, merchant_name: str | None = None) -> JSONObjectOrArray:
		"""
		Fetch one order document by id through the generic VTEX proxy.

		Args:
			order_id: VTEX order identifier.
			merchant_name: Optional seller account override resolved by Retail.

		Returns:
			The parsed JSON object or array returned by the proxy.

		Raises:
			VtexValidationError: If the order id is invalid.
			VtexConfigError: If Retail URL or auth token is missing (at construction).
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response is empty or not a JSON object/array.
		"""
		path = self.order_path(self.ORDER_DOCUMENT_PATH, order_id)
		return self.request(path=path, method='GET', merchant_name=merchant_name)

	def search_orders(self, raw_query: str) -> JSONObjectOrArray:
		"""
		Search orders through Retail's dedicated orders endpoint.

		Args:
			raw_query: Query string forwarded as Retail ``raw_query``. A leading
				``?`` is added when missing. The value is not re-encoded.

		Returns:
			The parsed JSON object or array returned by Retail.

		Raises:
			VtexValidationError: If the query is empty.
			VtexConfigError: If Retail URL or auth token is missing (at construction).
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response is empty or not a JSON object/array.
		"""
		query = self.normalize_raw_query(raw_query)
		response = self._client.post(self.ORDERS_SEARCH_PATH, json={'raw_query': query})
		if not isinstance(response, (dict, list)):
			raise VtexResponseError('Retail VTEX proxy returned a response that is not a JSON object or array.')
		return response
