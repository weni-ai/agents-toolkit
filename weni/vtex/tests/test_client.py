"""Tests for RetailClient configuration, POST execution, and error translation."""

from unittest.mock import MagicMock

import pytest
import requests

from weni.vtex.client import RetailClient
from weni.vtex.exceptions import VtexConfigError, VtexError, VtexHTTPError, VtexNetworkError, VtexResponseError
from weni.vtex.tests.conftest import create_context, default_project

BASE_URL = 'https://retail.example.com'
EXPECTED_HEADERS = {'Content-Type': 'application/json', 'Authorization': 'Bearer test-token'}


def make_response(status_code: int = 200, content: bytes = b'{}', json_value: object = None) -> MagicMock:
	"""Build a mocked requests.Response."""
	response = MagicMock()
	response.status_code = status_code
	response.content = content
	response.text = content.decode() if content else ''
	response.json.return_value = json_value
	response.raise_for_status.return_value = None
	return response


def make_error_response(status_code: int, text: str) -> MagicMock:
	"""Build a mocked non-2xx requests.Response."""
	response = MagicMock()
	response.status_code = status_code
	response.text = text
	response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
	return response


@pytest.fixture
def mock_request(mocker):
	"""Patch the transport call used by the client."""
	mock = mocker.patch('weni.vtex.client.requests.request')
	mock.return_value = make_response(json_value={'ok': True})
	return mock


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
	"""Ensure ambient environment variables don't leak into resolution tests."""
	monkeypatch.delenv('RETAIL_BASE_URL', raising=False)


class TestAuthTokenValidation:
	def test_missing_token_raises_config_error(self):
		with pytest.raises(VtexConfigError) as exc_info:
			RetailClient(create_context(project={'retail_url': BASE_URL}))

		assert 'auth_token' in str(exc_info.value)
		assert 'context.project' in str(exc_info.value)

	def test_missing_token_never_sends_request(self, mocker):
		mock_request = mocker.patch('weni.vtex.client.requests.request')

		with pytest.raises(VtexConfigError):
			RetailClient(create_context(project={'retail_url': BASE_URL}))

		mock_request.assert_not_called()


class TestBaseURLResolution:
	def test_project_takes_precedence_over_credentials(self):
		context = create_context(
			project=default_project(retail_url='https://retail.project'),
			credentials={'retail_url': 'https://retail.creds'},
		)

		assert RetailClient(context).base_url == 'https://retail.project'

	def test_credentials_take_precedence_over_globals(self):
		context = create_context(
			project={'auth_token': 'tk'},
			credentials={'retail_url': 'https://retail.creds'},
			globals={'retail_url': 'https://retail.globals'},
		)

		assert RetailClient(context).base_url == 'https://retail.creds'

	def test_globals_take_precedence_over_environment(self, monkeypatch):
		monkeypatch.setenv('RETAIL_BASE_URL', 'https://retail.env')
		context = create_context(project={'auth_token': 'tk'}, globals={'retail_url': 'https://retail.globals'})

		assert RetailClient(context).base_url == 'https://retail.globals'

	def test_environment_fallback(self, monkeypatch):
		monkeypatch.setenv('RETAIL_BASE_URL', 'https://retail.env')
		context = create_context(project={'auth_token': 'tk'})

		assert RetailClient(context).base_url == 'https://retail.env'

	def test_default_when_absent_everywhere(self):
		context = create_context(project={'auth_token': 'tk'})

		assert RetailClient(context).base_url == 'https://retailsetup.stg.cloud.weni.ai'
		assert RetailClient(context).base_url == RetailClient.DEFAULT_RETAIL_URL

	def test_trailing_slash_stripped(self):
		context = create_context(project=default_project(retail_url='https://retail.example.com/'))

		assert RetailClient(context).base_url == 'https://retail.example.com'


class TestPost:
	def test_posts_json_with_bearer_headers(self, mock_request):
		client = RetailClient(create_context(project=default_project()))
		result = client.post('/vtex/proxy/', json={'method': 'GET', 'path': '/api/oms/pvt/orders'})

		assert result == {'ok': True}
		mock_request.assert_called_once_with(
			'POST',
			f'{BASE_URL}/vtex/proxy/',
			headers=EXPECTED_HEADERS,
			json={'method': 'GET', 'path': '/api/oms/pvt/orders'},
		)

	@pytest.mark.parametrize(
		'retail_url, path',
		[
			('https://retail.example.com', '/vtex/proxy/'),
			('https://retail.example.com/', '/vtex/proxy/'),
			('https://retail.example.com', 'vtex/proxy/'),
			('https://retail.example.com/', 'vtex/proxy/'),
		],
	)
	def test_no_duplicate_or_missing_slashes(self, mock_request, retail_url, path):
		client = RetailClient(create_context(project=default_project(retail_url=retail_url)))
		client.post(path)

		assert mock_request.call_args[0][1] == 'https://retail.example.com/vtex/proxy/'

	def test_returns_parsed_list(self, mock_request):
		mock_request.return_value = make_response(json_value=[{'id': 1}, {'id': 2}])
		client = RetailClient(create_context(project=default_project()))

		assert client.post('/vtex/proxy/') == [{'id': 1}, {'id': 2}]

	def test_empty_body_returns_none(self, mock_request):
		mock_request.return_value = make_response(status_code=204, content=b'')
		client = RetailClient(create_context(project=default_project()))

		assert client.post('/vtex/proxy/') is None
		mock_request.return_value.json.assert_not_called()

	def test_request_without_body(self, mock_request):
		client = RetailClient(create_context(project=default_project()))
		client.post('/vtex/proxy/')

		assert mock_request.call_args.kwargs['json'] is None


class TestHTTPErrorTranslation:
	def test_non_2xx_raises_vtex_http_error(self, mocker):
		mock_request = mocker.patch('weni.vtex.client.requests.request')
		mock_request.return_value = make_error_response(400, '{"detail": "Invalid"}')
		client = RetailClient(create_context(project=default_project()))

		with pytest.raises(VtexHTTPError) as exc_info:
			client.post('/vtex/proxy/', json={'method': 'GET', 'path': '/api/test'})

		assert exc_info.value.status_code == 400
		assert exc_info.value.response_body == '{"detail": "Invalid"}'
		assert isinstance(exc_info.value.__cause__, requests.exceptions.HTTPError)

	def test_base_type_catches_http_error(self, mocker):
		mocker.patch(
			'weni.vtex.client.requests.request',
			return_value=make_error_response(404, 'Not found'),
		)
		client = RetailClient(create_context(project=default_project()))

		with pytest.raises(VtexError):
			client.post('/vtex/proxy/')


class TestNetworkErrorTranslation:
	def test_transport_failure_raises_vtex_network_error(self, mocker):
		mocker.patch(
			'weni.vtex.client.requests.request',
			side_effect=requests.exceptions.ConnectionError('Connection refused'),
		)
		client = RetailClient(create_context(project=default_project()))

		with pytest.raises(VtexNetworkError) as exc_info:
			client.post('/vtex/proxy/')

		assert 'Connection refused' in str(exc_info.value)
		assert isinstance(exc_info.value.__cause__, requests.exceptions.ConnectionError)


class TestResponseErrorTranslation:
	def test_malformed_body_raises_vtex_response_error(self, mocker):
		response = MagicMock()
		response.status_code = 200
		response.content = b'not json'
		response.raise_for_status.return_value = None
		response.json.side_effect = ValueError('No JSON object could be decoded')
		mocker.patch('weni.vtex.client.requests.request', return_value=response)
		client = RetailClient(create_context(project=default_project()))

		with pytest.raises(VtexResponseError) as exc_info:
			client.post('/vtex/proxy/')

		assert isinstance(exc_info.value.__cause__, ValueError)
