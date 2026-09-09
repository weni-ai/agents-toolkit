"""
VTEX facade for forwarding private VTEX API calls during tool execution.
"""

from typing import TYPE_CHECKING, Any

from weni.vtex.exceptions import VtexValidationError

if TYPE_CHECKING:  # pragma: no cover
	from weni.tool import Tool
	from weni.vtex.sender import VtexSender


class Vtex:
	"""
	Tool-bound facade for generic VTEX proxy operations.

	Example:
		```python
		from weni.vtex import Vtex

		class MyTool(Tool):
		    def execute(self, context: Context):
		        orders = Vtex(self).request(path='/api/oms/pvt/orders', method='GET')
		```

	Shorthand via Tool:
		``self.gallery_vtex(endpoint=...)`` is equivalent to ``self.vtex.request(endpoint=...)``.
	"""

	# Exposes self.gallery_vtex on any Tool without adding methods to Tool.
	_tool_methods: dict[str, str] = {
		'gallery_vtex': 'request',
	}

	def __init__(self, tool: 'Tool'):
		self._tool = tool

	def _get_sender(self) -> 'VtexSender':
		from weni.vtex.sender import VtexSender

		return VtexSender(self._tool.context)

	def request(
		self,
		path: str | None = None,
		endpoint: str | None = None,
		method: str = 'GET',
		headers: dict[str, Any] | None = None,
		data: dict[str, Any] | list[Any] | None = None,
		params: dict[str, Any] | None = None,
		merchant_name: str | None = None,
	) -> dict[str, Any] | list[Any]:
		"""
		Forward a VTEX API call through Retail's generic proxy.

		Args:
			path: VTEX API path (leading slash optional). Takes precedence over ``endpoint``.
			endpoint: Alias for ``path``.
			method: HTTP method. Allowed: GET, POST, PUT, PATCH. Defaults to GET.
			headers: Optional headers forwarded to VTEX (not used for Retail auth).
			data: Optional JSON body for POST, PUT, or PATCH.
			params: Optional query parameters appended to the VTEX URL.
			merchant_name: Optional seller account override resolved by Retail.

		Returns:
			The parsed JSON object or array returned by the proxy.

		Raises:
			VtexValidationError: If path/endpoint is missing or method/path is invalid.
			VtexConfigError: If Retail URL or auth token is missing.
			VtexHTTPError: If Retail responds with a non-success status.
			VtexNetworkError: If the request fails before a response is received.
			VtexResponseError: If a success response is empty or not a JSON object/array.
		"""
		target = path if path is not None else endpoint
		if target is None:
			raise VtexValidationError('path or endpoint is required.')

		from weni.vtex.sender import VtexSender

		result = self._get_sender().request(
			path=target,
			method=method,
			headers=headers,
			data=data,
			params=params,
			merchant_name=merchant_name,
		)
		self._tool._register_operation(
			'vtex_requests',
			{'path': VtexSender.normalize_path(target), 'method': method.upper()},
		)
		return result
