"""Shared test helpers for the VTEX package."""

from weni.context import Context


def create_context(
	project: dict | None = None,
	credentials: dict | None = None,
	globals: dict | None = None,
	contact: dict | None = None,
	parameters: dict | None = None,
) -> Context:
	"""Create a Context for VTEX integration tests."""
	return Context(
		credentials=credentials or {},
		parameters=parameters or {},
		globals=globals or {},
		contact=contact or {},
		project=project or {},
		constants={},
	)


def default_project(**overrides) -> dict:
	"""Return a default project mapping with auth token and Retail URL."""
	base = {'retail_url': 'https://retail.example.com', 'auth_token': 'test-token'}
	base.update(overrides)
	return base
