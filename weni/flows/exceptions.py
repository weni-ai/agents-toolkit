"""
Typed error hierarchy for the Flows client.

All errors raised by the client subclass :class:`FlowsClientError`, so
integrations can handle every failure mode (configuration, HTTP, network,
response parsing) with a single catch.
"""


class FlowsClientError(Exception):
	"""Base error for all Flows client failures."""


class FlowsClientConfigError(FlowsClientError):
	"""Raised when a required configuration value cannot be resolved."""


class FlowsHTTPError(FlowsClientError):
	"""
	Raised when Flows responds with a non-success status.

	Attributes:
		status_code: The HTTP status code returned by Flows.
		response_body: The raw response body returned by Flows.
	"""

	def __init__(self, status_code: int, response_body: str):
		self.status_code = status_code
		self.response_body = response_body
		super().__init__(f'Flows API returned {status_code}: {response_body}')


class FlowsNetworkError(FlowsClientError):
	"""Raised when the request fails before a response is received."""


class FlowsResponseError(FlowsClientError):
	"""Raised when a success response carries a body that cannot be parsed."""
