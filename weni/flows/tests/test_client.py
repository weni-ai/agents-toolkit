"""
Tests for FlowsClient request execution (User Story 1).

Covers verb delegation, URL building, header construction, payload
forwarding, and response parsing — all with the network layer mocked.
"""

from unittest.mock import MagicMock

import pytest

from weni.flows import FlowsClient

BASE_URL = 'https://flows.example.com'
PROJECT = {'flows_url': BASE_URL, 'auth_token': 'test-token'}
EXPECTED_HEADERS = {'Content-Type': 'application/json', 'Authorization': 'Bearer test-token'}


def make_response(status_code: int = 200, content: bytes = b'{}', json_value: object = None) -> MagicMock:
	"""Build a mocked requests.Response."""
	response = MagicMock()
	response.status_code = status_code
	response.content = content
	response.json.return_value = json_value
	response.raise_for_status.return_value = None
	return response


@pytest.fixture
def mock_request(mocker):
	"""Patch the transport call used by the client."""
	mock = mocker.patch('weni.flows.client.requests.request')
	mock.return_value = make_response(json_value={'ok': True})
	return mock


class TestVerbs:
	def test_get(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		result = client.get('/api/v2/things.json')

		assert result == {'ok': True}
		mock_request.assert_called_once_with(
			'GET',
			f'{BASE_URL}/api/v2/things.json',
			headers=EXPECTED_HEADERS,
			json=None,
			params=None,
		)

	def test_post(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		result = client.post('/api/v2/things.json', json={'k': 'v'})

		assert result == {'ok': True}
		mock_request.assert_called_once_with(
			'POST',
			f'{BASE_URL}/api/v2/things.json',
			headers=EXPECTED_HEADERS,
			json={'k': 'v'},
			params=None,
		)

	def test_put(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.put('/api/v2/things/1.json', json={'k': 'v'})

		assert mock_request.call_args[0][0] == 'PUT'

	def test_patch(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.patch('/api/v2/things/1.json', json={'k': 'v'})

		assert mock_request.call_args[0][0] == 'PATCH'

	def test_delete(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.delete('/api/v2/things/1.json')

		assert mock_request.call_args[0][0] == 'DELETE'
		assert mock_request.call_args.kwargs['json'] is None


class TestURLBuilding:
	@pytest.mark.parametrize(
		'flows_url, path',
		[
			('https://flows.example.com', '/api/test'),
			('https://flows.example.com/', '/api/test'),
			('https://flows.example.com', 'api/test'),
			('https://flows.example.com/', 'api/test'),
		],
	)
	def test_no_duplicate_or_missing_slashes(self, make_context, mock_request, flows_url, path):
		client = FlowsClient(make_context(project={'flows_url': flows_url, 'auth_token': 'tk'}))
		client.get(path)

		assert mock_request.call_args[0][1] == 'https://flows.example.com/api/test'


class TestHeaders:
	def test_content_type_and_bearer_token(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.get('/api/test')

		assert mock_request.call_args.kwargs['headers'] == EXPECTED_HEADERS


class TestPayloads:
	def test_params_forwarded(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.get('/api/test', params={'page': 2})

		assert mock_request.call_args.kwargs['params'] == {'page': 2}

	def test_request_without_body(self, make_context, mock_request):
		client = FlowsClient(make_context(project=PROJECT))
		client.post('/api/test')

		assert mock_request.call_args.kwargs['json'] is None


class TestResponseParsing:
	def test_returns_parsed_dict(self, make_context, mock_request):
		mock_request.return_value = make_response(json_value={'id': 1})
		client = FlowsClient(make_context(project=PROJECT))

		assert client.get('/api/test') == {'id': 1}

	def test_returns_parsed_list(self, make_context, mock_request):
		mock_request.return_value = make_response(json_value=[{'id': 1}, {'id': 2}])
		client = FlowsClient(make_context(project=PROJECT))

		assert client.get('/api/test') == [{'id': 1}, {'id': 2}]

	def test_empty_body_returns_none(self, make_context, mock_request):
		mock_request.return_value = make_response(status_code=204, content=b'')
		client = FlowsClient(make_context(project=PROJECT))

		assert client.delete('/api/test') is None
		mock_request.return_value.json.assert_not_called()
