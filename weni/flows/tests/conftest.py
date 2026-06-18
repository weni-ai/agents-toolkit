"""Shared fixtures for the Flows client test suite."""

from typing import Callable

import pytest

from weni.context import Context


@pytest.fixture
def make_context() -> Callable[..., Context]:
	"""Factory fixture building a Context with only the relevant namespaces filled."""

	def _make_context(
		project: dict | None = None,
		credentials: dict | None = None,
		globals: dict | None = None,
		contact: dict | None = None,
		parameters: dict | None = None,
	) -> Context:
		return Context(
			credentials=credentials or {},
			parameters=parameters or {},
			globals=globals or {},
			contact=contact or {},
			project=project or {},
			constants={},
		)

	return _make_context
