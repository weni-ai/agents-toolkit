"""Tests for VtexSender path/method validation and proxy payload construction."""

from unittest.mock import MagicMock, patch

import pytest

from weni.vtex.exceptions import VtexConfigError, VtexHTTPError, VtexResponseError, VtexValidationError
from weni.vtex.sender import VtexSender
from weni.vtex.tests.conftest import create_context, default_project


def _sender(mock_client=None):
	mock_client = mock_client or MagicMock()
	with patch('weni.vtex.sender.RetailClient', return_value=mock_client):
		sender = VtexSender(create_context(project=default_project()))
	return sender, mock_client


class TestVtexSenderInit:
	def test_proxy_path_constant(self):
		assert VtexSender.PROXY_PATH == '/vtex/proxy/'

	def test_maps_client_config_error(self):
		with pytest.raises(VtexConfigError, match='auth_token'):
			VtexSender(create_context(project={'retail_url': 'https://retail.example.com'}))


class TestNormalizePath:
	def test_adds_leading_slash(self):
		assert VtexSender.normalize_path('api/oms/pvt/orders') == '/api/oms/pvt/orders'

	def test_keeps_existing_slash(self):
		assert VtexSender.normalize_path('/api/oms/pvt/orders') == '/api/oms/pvt/orders'

	def test_strips_whitespace(self):
		assert VtexSender.normalize_path('  /api/oms/pvt/orders  ') == '/api/oms/pvt/orders'

	def test_empty_raises(self):
		with pytest.raises(VtexValidationError, match='must not be empty'):
			VtexSender.normalize_path('')

	def test_whitespace_only_raises(self):
		with pytest.raises(VtexValidationError, match='must not be empty'):
			VtexSender.normalize_path('   ')

	@pytest.mark.parametrize(
		'url', ['http://evil.example/api', 'https://evil.example/api', 'HTTPS://evil.example/api']
	)
	def test_absolute_url_raises(self, url):
		with pytest.raises(VtexValidationError, match='absolute URL'):
			VtexSender.normalize_path(url)


class TestRequestValidation:
	def test_disallowed_method_never_posts(self):
		sender, client = _sender()
		client.post.return_value = {'ok': True}

		with pytest.raises(VtexValidationError, match='DELETE'):
			sender.request(path='/api/oms/pvt/orders', method='DELETE')

		client.post.assert_not_called()

	def test_invalid_path_never_posts(self):
		sender, client = _sender()

		with pytest.raises(VtexValidationError, match='absolute URL'):
			sender.request(path='https://store.myvtex.com/api/oms/pvt/orders')

		client.post.assert_not_called()


class TestRequestPayload:
	def test_minimal_get_payload(self):
		sender, client = _sender()
		client.post.return_value = {'orders': []}

		result = sender.request(path='api/oms/pvt/orders')

		assert result == {'orders': []}
		client.post.assert_called_once_with(
			'/vtex/proxy/',
			json={'method': 'GET', 'path': '/api/oms/pvt/orders'},
		)

	def test_lowercased_method_is_uppercased(self):
		sender, client = _sender()
		client.post.return_value = {}

		sender.request(path='/api/catalog', method='patch')

		assert client.post.call_args.kwargs['json']['method'] == 'PATCH'

	@pytest.mark.parametrize('method', ['GET', 'POST', 'PUT', 'PATCH'])
	def test_allowed_methods(self, method):
		sender, client = _sender()
		client.post.return_value = {}

		sender.request(path='/api/test', method=method)

		assert client.post.call_args.kwargs['json']['method'] == method

	def test_optional_fields_included_when_provided(self):
		sender, client = _sender()
		client.post.return_value = {'ok': True}

		sender.request(
			path='/api/oms/pvt/orders',
			method='POST',
			headers={'Accept': 'application/json'},
			data={'customer': 'a@b.com'},
			params={'f_status': 'ready-for-handling'},
			merchant_name='selleraccount',
		)

		client.post.assert_called_once_with(
			'/vtex/proxy/',
			json={
				'method': 'POST',
				'path': '/api/oms/pvt/orders',
				'headers': {'Accept': 'application/json'},
				'data': {'customer': 'a@b.com'},
				'params': {'f_status': 'ready-for-handling'},
				'merchant_name': 'selleraccount',
			},
		)

	def test_empty_headers_and_params_omitted(self):
		sender, client = _sender()
		client.post.return_value = {}

		sender.request(path='/api/test', headers={}, params={}, merchant_name='')

		assert client.post.call_args.kwargs['json'] == {'method': 'GET', 'path': '/api/test'}

	def test_empty_data_is_forwarded(self):
		sender, client = _sender()
		client.post.return_value = {}

		sender.request(path='/api/test', method='POST', data={})

		assert client.post.call_args.kwargs['json']['data'] == {}

	def test_empty_list_data_is_forwarded(self):
		sender, client = _sender()
		client.post.return_value = []

		result = sender.request(path='/api/test', method='POST', data=[])

		assert result == []
		assert client.post.call_args.kwargs['json']['data'] == []


class TestRequestResponse:
	def test_rejects_empty_success_body(self):
		sender, client = _sender()
		client.post.return_value = None

		with pytest.raises(VtexResponseError, match='not a JSON object or array'):
			sender.request(path='/api/oms/pvt/orders')

	def test_rejects_non_object_json(self):
		sender, client = _sender()
		client.post.return_value = 'plain-string'

		with pytest.raises(VtexResponseError, match='not a JSON object or array'):
			sender.request(path='/api/oms/pvt/orders')

	def test_propagates_http_error(self):
		sender, client = _sender()
		client.post.side_effect = VtexHTTPError(502, 'bad gateway')

		with pytest.raises(VtexHTTPError) as exc_info:
			sender.request(path='/api/oms/pvt/orders')

		assert exc_info.value.status_code == 502
