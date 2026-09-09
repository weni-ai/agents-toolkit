"""Tests for the VTEX error hierarchy."""

import pytest

from weni.vtex.exceptions import (
	VtexConfigError,
	VtexError,
	VtexHTTPError,
	VtexNetworkError,
	VtexResponseError,
	VtexValidationError,
)


class TestErrorHierarchy:
	@pytest.mark.parametrize(
		'error_type',
		[VtexConfigError, VtexValidationError, VtexHTTPError, VtexNetworkError, VtexResponseError],
	)
	def test_all_errors_subclass_base(self, error_type):
		assert issubclass(error_type, VtexError)

	def test_http_error_exposes_status_and_body(self):
		error = VtexHTTPError(502, '{"detail": "upstream"}')

		assert error.status_code == 502
		assert error.response_body == '{"detail": "upstream"}'
		assert '502' in str(error)
		assert 'upstream' in str(error)
