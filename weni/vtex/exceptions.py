"""
Typed error hierarchy for the VTEX proxy integration.

All errors raised by the client, sender, and facade subclass :class:`VtexError`,
so callers can handle every failure mode with a single catch.
"""


class VtexError(Exception):
	"""Base error for all VTEX integration failures."""


class VtexConfigError(VtexError):
	"""Raised when a required configuration value cannot be resolved."""


class VtexValidationError(VtexError):
	"""Raised when a request argument is invalid before any outbound call."""


class VtexHTTPError(VtexError):
	"""
	Raised when Retail responds with a non-success status.

	Attributes:
		status_code: The HTTP status code returned by Retail.
		response_body: The raw response body returned by Retail.
	"""

	def __init__(self, status_code: int, response_body: str):
		self.status_code = status_code
		self.response_body = response_body
		super().__init__(f'Retail VTEX proxy returned {status_code}: {response_body}')


class VtexNetworkError(VtexError):
	"""Raised when the request fails before a response is received."""


class VtexResponseError(VtexError):
	"""Raised when a success response carries a body that cannot be used."""
