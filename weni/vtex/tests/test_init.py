"""Tests for weni.vtex public exports and Tool registration."""

from weni import Tool
from weni import vtex
from weni.vtex.vtex import Vtex


def test_public_exports():
	assert set(vtex.__all__) == {
		'RetailClient',
		'Vtex',
		'VtexConfigError',
		'VtexError',
		'VtexHTTPError',
		'VtexNetworkError',
		'VtexResponseError',
		'VtexSender',
		'VtexValidationError',
	}

	for name in vtex.__all__:
		assert hasattr(vtex, name)


def test_tool_registers_vtex_facade():
	assert Tool._FACADE_REGISTRY['vtex'] is Vtex
