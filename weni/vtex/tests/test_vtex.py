"""Tests for the Vtex facade, operation log, and Tool shorthand."""

from unittest.mock import MagicMock, patch

import pytest

from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
from weni.vtex.exceptions import VtexValidationError
from weni.vtex.tests.conftest import create_context, default_project
from weni.vtex.vtex import Vtex


def tool_with_context(project: dict | None = None) -> MagicMock:
	mock_tool = MagicMock()
	mock_tool.context = create_context(project=project or default_project())
	return mock_tool


class TestVtexFacade:
	@patch('weni.vtex.sender.VtexSender')
	def test_request_delegates_to_sender(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.request.return_value = {'orders': []}
		mock_sender_class.return_value = mock_sender

		mock_tool = tool_with_context()
		result = Vtex(mock_tool).request(path='/api/oms/pvt/orders', method='GET')

		mock_sender_class.assert_called_once_with(mock_tool.context)
		mock_sender.request.assert_called_once_with(
			path='/api/oms/pvt/orders',
			method='GET',
			headers=None,
			data=None,
			params=None,
			merchant_name=None,
		)
		assert result == {'orders': []}

	@patch('weni.vtex.sender.VtexSender')
	def test_endpoint_alias(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.request.return_value = {}
		mock_sender_class.return_value = mock_sender

		Vtex(tool_with_context()).request(endpoint='api/oms/pvt/orders', method='GET')

		mock_sender.request.assert_called_once_with(
			path='api/oms/pvt/orders',
			method='GET',
			headers=None,
			data=None,
			params=None,
			merchant_name=None,
		)

	@patch('weni.vtex.sender.VtexSender')
	def test_path_wins_over_endpoint(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.request.return_value = {}
		mock_sender_class.return_value = mock_sender

		Vtex(tool_with_context()).request(path='/api/from-path', endpoint='/api/from-endpoint')

		assert mock_sender.request.call_args.kwargs['path'] == '/api/from-path'

	def test_missing_path_and_endpoint_raises_before_sender(self):
		mock_tool = tool_with_context()

		with pytest.raises(VtexValidationError, match='path or endpoint is required'):
			Vtex(mock_tool).request(method='GET')

		mock_tool._register_operation.assert_not_called()

	@patch('weni.vtex.sender.VtexSender')
	def test_forwards_optional_arguments(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.request.return_value = {'ok': True}
		mock_sender_class.return_value = mock_sender

		Vtex(tool_with_context()).request(
			path='/api/oms/pvt/orders',
			method='POST',
			headers={'Accept': 'application/json'},
			data={'a': 1},
			params={'page': 1},
			merchant_name='seller',
		)

		mock_sender.request.assert_called_once_with(
			path='/api/oms/pvt/orders',
			method='POST',
			headers={'Accept': 'application/json'},
			data={'a': 1},
			params={'page': 1},
			merchant_name='seller',
		)


class TestVtexOperationLog:
	@patch.object(Vtex, '_get_sender')
	def test_registers_path_and_method_after_success(self, mock_get_sender):
		mock_get_sender.return_value.request.return_value = {'ok': True}
		mock_tool = tool_with_context()

		Vtex(mock_tool).request(endpoint='api/oms/pvt/orders', method='get')

		mock_tool._register_operation.assert_called_once_with(
			'vtex_requests',
			{'path': '/api/oms/pvt/orders', 'method': 'GET'},
		)

	@patch.object(Vtex, '_get_sender')
	def test_does_not_log_headers_or_data(self, mock_get_sender):
		mock_get_sender.return_value.request.return_value = {'ok': True}
		mock_tool = tool_with_context()

		Vtex(mock_tool).request(
			path='/api/oms/pvt/orders',
			headers={'X-VTEX-API-AppToken': 'secret'},
			data={'token': 'secret'},
		)

		logged = mock_tool._register_operation.call_args[0][1]
		assert logged == {'path': '/api/oms/pvt/orders', 'method': 'GET'}
		assert 'headers' not in logged
		assert 'data' not in logged

	@patch.object(Vtex, '_get_sender')
	def test_does_not_register_operation_when_sender_fails(self, mock_get_sender):
		mock_get_sender.return_value.request.side_effect = VtexValidationError('invalid')
		mock_tool = tool_with_context()

		with pytest.raises(VtexValidationError, match='invalid'):
			Vtex(mock_tool).request(path='/api/oms/pvt/orders')

		mock_tool._register_operation.assert_not_called()


class TestToolShorthand:
	def test_requesting_vtex_is_bound_to_request(self, mocker):
		mock_client = MagicMock()
		mock_client.post.return_value = {'orders': []}
		mocker.patch('weni.vtex.sender.RetailClient', return_value=mock_client)

		class ProbeTool(Tool):
			def execute(self, context: Context):
				result = self.requesting_vtex(endpoint='api/oms/pvt/orders', method='GET')
				namespaced = self.vtex.request(path='/api/oms/pvt/orders', method='GET')
				assert result == namespaced
				return TextResponse(data=result)

		context = create_context(project=default_project())
		result, _format, _events, _traces = ProbeTool(context)

		assert result['result'] == {'orders': []}
		assert result['vtex_requests'] == [
			{'path': '/api/oms/pvt/orders', 'method': 'GET'},
			{'path': '/api/oms/pvt/orders', 'method': 'GET'},
		]
		assert mock_client.post.call_count == 2


class TestOrderFacade:
	@patch.object(Vtex, '_get_sender')
	def test_get_order_delegates_through_request(self, mock_get_sender):
		mock_get_sender.return_value.request.return_value = {'orderId': 'v1-01'}
		mock_tool = tool_with_context()

		result = Vtex(mock_tool).get_order('v1-01', merchant_name='seller')

		assert result == {'orderId': 'v1-01'}
		mock_get_sender.return_value.request.assert_called_once_with(
			path='/api/oms/pvt/orders/v1-01',
			method='GET',
			headers=None,
			data=None,
			params=None,
			merchant_name='seller',
		)
		mock_tool._register_operation.assert_called_once_with(
			'vtex_requests',
			{'path': '/api/oms/pvt/orders/v1-01', 'method': 'GET'},
		)

	@patch.object(Vtex, '_get_sender')
	def test_get_order_document_delegates_through_request(self, mock_get_sender):
		mock_get_sender.return_value.request.return_value = {'orderId': 'v1-01'}
		mock_tool = tool_with_context()

		Vtex(mock_tool).get_order_document(' v1-01 ')

		mock_get_sender.return_value.request.assert_called_once_with(
			path='/api/orders/pvt/document/v1-01',
			method='GET',
			headers=None,
			data=None,
			params=None,
			merchant_name=None,
		)

	def test_invalid_order_id_does_not_log(self):
		mock_tool = tool_with_context()

		with pytest.raises(VtexValidationError, match='path separators'):
			Vtex(mock_tool).get_order('a/b')

		mock_tool._register_operation.assert_not_called()

	@patch.object(Vtex, '_get_sender')
	def test_search_orders_logs_path_without_query(self, mock_get_sender):
		mock_get_sender.return_value.search_orders.return_value = {'list': []}
		mock_tool = tool_with_context()

		result = Vtex(mock_tool).search_orders('?q=user@email.com')

		assert result == {'list': []}
		mock_get_sender.return_value.search_orders.assert_called_once_with('?q=user@email.com')
		logged = mock_tool._register_operation.call_args[0][1]
		assert logged == {'path': '/vtex/orders/', 'method': 'POST'}
		assert 'user@email.com' not in str(logged)

	@patch.object(Vtex, '_get_sender')
	def test_search_orders_does_not_log_when_sender_fails(self, mock_get_sender):
		mock_get_sender.return_value.search_orders.side_effect = VtexValidationError('empty')
		mock_tool = tool_with_context()

		with pytest.raises(VtexValidationError, match='empty'):
			Vtex(mock_tool).search_orders('')

		mock_tool._register_operation.assert_not_called()


class TestOrderToolShorthand:
	def test_order_helpers_are_bound(self, mocker):
		mock_client = MagicMock()
		mock_client.post.side_effect = [
			{'orderId': 'v1-01'},
			{'document': True},
			{'list': []},
		]
		mocker.patch('weni.vtex.sender.RetailClient', return_value=mock_client)

		class ProbeTool(Tool):
			def execute(self, context: Context):
				order = self.get_order('v1-01')
				document = self.get_order_document('v1-01')
				found = self.search_orders('q=user@email.com')
				assert order == {'orderId': 'v1-01'}
				assert document == {'document': True}
				assert found == {'list': []}
				return TextResponse(data=order)

		context = create_context(project=default_project())
		result, _format, _events, _traces = ProbeTool(context)

		assert result['vtex_requests'] == [
			{'path': '/api/oms/pvt/orders/v1-01', 'method': 'GET'},
			{'path': '/api/orders/pvt/document/v1-01', 'method': 'GET'},
			{'path': '/vtex/orders/', 'method': 'POST'},
		]
		assert mock_client.post.call_args_list[0].args == ('/vtex/proxy/',)
		assert mock_client.post.call_args_list[0].kwargs == {
			'json': {'method': 'GET', 'path': '/api/oms/pvt/orders/v1-01'},
		}
		assert mock_client.post.call_args_list[1].kwargs == {
			'json': {'method': 'GET', 'path': '/api/orders/pvt/document/v1-01'},
		}
		assert mock_client.post.call_args_list[2].args == ('/vtex/orders/',)
		assert mock_client.post.call_args_list[2].kwargs == {
			'json': {'raw_query': '?q=user@email.com'},
		}
