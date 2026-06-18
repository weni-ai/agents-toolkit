"""
Tests for FlowsClient error translation and hierarchy (User Story 3).

Covers HTTP errors, network failures, unreadable response bodies, and the
single-catch guarantee of the FlowsClientError base type.
"""

from unittest.mock import MagicMock

import pytest
import requests

from weni.flows import (
	FlowsClient,
	FlowsClientConfigError,
	FlowsClientError,
	FlowsHTTPError,
	FlowsNetworkError,
	FlowsResponseError,
)

PROJECT = {'flows_url': 'https://flows.example.com', 'auth_token': 'tk'}


def make_error_response(status_code: int, text: str) -> MagicMock:
	"""Build a mocked non-2xx requests.Response."""
	response = MagicMock()
	response.status_code = status_code
	response.text = text
	response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
	return response


class TestHTTPErrorTranslation:
	def test_non_2xx_raises_flows_http_error(self, make_context, mocker):
		mock_request = mocker.patch('weni.flows.client.requests.request')
		mock_request.return_value = make_error_response(400, '{"detail": "Invalid"}')
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsHTTPError) as exc_info:
			client.post('/api/test', json={'k': 'v'})

		assert exc_info.value.status_code == 400
		assert exc_info.value.response_body == '{"detail": "Invalid"}'
		assert '400' in str(exc_info.value)

	def test_original_exception_chained(self, make_context, mocker):
		mock_request = mocker.patch('weni.flows.client.requests.request')
		mock_request.return_value = make_error_response(500, 'Server error')
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsHTTPError) as exc_info:
			client.get('/api/test')

		assert isinstance(exc_info.value.__cause__, requests.exceptions.HTTPError)


class TestNetworkErrorTranslation:
	def test_transport_failure_raises_flows_network_error(self, make_context, mocker):
		mock_request = mocker.patch('weni.flows.client.requests.request')
		mock_request.side_effect = requests.exceptions.ConnectionError('Connection refused')
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsNetworkError) as exc_info:
			client.get('/api/test')

		assert 'Connection refused' in str(exc_info.value)
		assert isinstance(exc_info.value.__cause__, requests.exceptions.ConnectionError)


class TestResponseErrorTranslation:
	def test_malformed_body_raises_flows_response_error(self, make_context, mocker):
		response = MagicMock()
		response.status_code = 200
		response.content = b'not json'
		response.raise_for_status.return_value = None
		response.json.side_effect = ValueError('No JSON object could be decoded')
		mocker.patch('weni.flows.client.requests.request', return_value=response)
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsResponseError) as exc_info:
			client.get('/api/test')

		assert isinstance(exc_info.value.__cause__, ValueError)


class TestErrorHierarchy:
	@pytest.mark.parametrize(
		'error_type',
		[FlowsClientConfigError, FlowsHTTPError, FlowsNetworkError, FlowsResponseError],
	)
	def test_all_errors_subclass_base(self, error_type):
		assert issubclass(error_type, FlowsClientError)

	def test_base_type_catches_config_error(self, make_context):
		with pytest.raises(FlowsClientError):
			FlowsClient(make_context())

	def test_base_type_catches_http_error(self, make_context, mocker):
		mock_request = mocker.patch('weni.flows.client.requests.request')
		mock_request.return_value = make_error_response(404, 'Not found')
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsClientError):
			client.get('/api/test')

	def test_base_type_catches_network_error(self, make_context, mocker):
		mocker.patch('weni.flows.client.requests.request', side_effect=requests.exceptions.Timeout('timed out'))
		client = FlowsClient(make_context(project=PROJECT))

		with pytest.raises(FlowsClientError):
			client.get('/api/test')
