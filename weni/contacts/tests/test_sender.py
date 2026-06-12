"""Tests for ContactSender."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from weni.contacts.sender import (
	ContactAmbiguousError,
	ContactNotFoundError,
	ContactSender,
	ContactSenderConfigError,
	ContactSenderError,
	ContactValidationError,
)
from weni.contacts.tests.conftest import create_context, default_project
from weni.flows.exceptions import (
	FlowsClientConfigError,
	FlowsClientError,
	FlowsHTTPError,
	FlowsNetworkError,
	FlowsResponseError,
)

CONTACT = {
	'uuid': 'abc-123',
	'name': 'Leonardo',
	'fields': {'email': 'a@b.com'},
	'urns': ['whatsapp:5582999893640'],
}
LIST_ONE: dict[str, Any] = {'results': [CONTACT], 'next': None, 'previous': None}
LIST_EMPTY: dict[str, Any] = {'results': [], 'next': None, 'previous': None}


def _sender(context=None, mock_client=None):
	mock_client = mock_client or MagicMock()
	with patch('weni.contacts.sender.FlowsClient', return_value=mock_client):
		sender = ContactSender(context or create_context(project=default_project()))
	return sender, mock_client


class TestContactSenderInit:
	def test_maps_flows_client_config_error(self):
		with patch('weni.contacts.sender.FlowsClient', side_effect=FlowsClientConfigError('missing token')):
			with pytest.raises(ContactSenderConfigError, match='missing token'):
				ContactSender(create_context(project={}))

	def test_contacts_path_constant(self):
		assert ContactSender.CONTACTS_PATH == '/api/v2/contacts.json'


class TestContactSenderUrnResolution:
	def test_from_urns_list(self):
		context = create_context(
			project=default_project(),
			contact={'urns': ['whatsapp:5511999999999', 'tel:+5511999999999']},
		)
		sender, _ = _sender(context)
		assert sender._get_contact_urn() == 'whatsapp:5511999999999'

	def test_from_urn_field(self):
		context = create_context(project=default_project(), contact={'urn': 'whatsapp:5511999999999'})
		sender, _ = _sender(context)
		assert sender._get_contact_urn() == 'whatsapp:5511999999999'

	def test_from_parameters_fallback(self):
		context = create_context(
			project=default_project(),
			parameters={'contact_urn': 'whatsapp:5584988242399'},
		)
		sender, _ = _sender(context)
		assert sender._get_contact_urn() == 'whatsapp:5584988242399'

	def test_contact_takes_priority_over_parameters(self):
		context = create_context(
			project=default_project(),
			contact={'urns': ['whatsapp:5511999999999']},
			parameters={'contact_urn': 'whatsapp:5584988242399'},
		)
		sender, _ = _sender(context)
		assert sender._resolve_urn(None) == 'whatsapp:5511999999999'

	def test_explicit_urn_override(self):
		sender, _ = _sender()
		assert sender._resolve_urn('whatsapp:override') == 'whatsapp:override'

	def test_missing_urn_raises_config_error(self):
		sender, _ = _sender()
		with pytest.raises(ContactSenderConfigError, match='contact URN not found'):
			sender._resolve_urn(None)


class TestAlternateWhatsappBrazilUrn:
	def test_remove_ninth_digit(self):
		urn = 'whatsapp:5582999893640'
		assert ContactSender._alternate_whatsapp_brazil_urn(urn) == 'whatsapp:558299893640'

	def test_insert_ninth_digit(self):
		urn = 'whatsapp:558299893640'
		assert ContactSender._alternate_whatsapp_brazil_urn(urn) == 'whatsapp:5582999893640'

	def test_non_brazil_returns_none(self):
		assert ContactSender._alternate_whatsapp_brazil_urn('whatsapp:14155552671') is None
		assert ContactSender._alternate_whatsapp_brazil_urn('tel:+5511999999999') is None


class TestContactSenderGet:
	def test_get_unwraps_single_result(self):
		sender, client = _sender(
			create_context(
				project=default_project(),
				contact={'urns': ['whatsapp:5582999893640']},
			)
		)
		client.get.return_value = LIST_ONE

		result = sender.get()

		assert result == CONTACT
		client.get.assert_called_once_with('/api/v2/contacts.json', params={'urn': 'whatsapp:5582999893640'})

	def test_get_with_explicit_urn_override(self):
		sender, client = _sender()
		client.get.return_value = LIST_ONE

		sender.get(urn='whatsapp:override')

		client.get.assert_called_once_with('/api/v2/contacts.json', params={'urn': 'whatsapp:override'})

	def test_get_empty_results_raises_not_found(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:14155552671']})
		)
		client.get.return_value = LIST_EMPTY

		with pytest.raises(ContactNotFoundError):
			sender.get()

	def test_get_multiple_results_raises_ambiguous(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = {'results': [CONTACT, CONTACT], 'next': None, 'previous': None}

		with pytest.raises(ContactAmbiguousError):
			sender.get()

	def test_get_not_found_when_alternate_retry_also_empty(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = [LIST_EMPTY, LIST_EMPTY]

		with pytest.raises(ContactNotFoundError):
			sender.get()

		assert client.get.call_count == 2

	def test_get_retries_ninth_digit_variant(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		alternate_contact = {**CONTACT, 'urns': ['whatsapp:558299893640']}
		client.get.side_effect = [LIST_EMPTY, {'results': [alternate_contact], 'next': None, 'previous': None}]

		result = sender.get()

		assert result == alternate_contact
		assert client.get.call_args_list[0].kwargs == {'params': {'urn': 'whatsapp:5582999893640'}}
		assert client.get.call_args_list[1].kwargs == {'params': {'urn': 'whatsapp:558299893640'}}

	def test_get_skips_retry_for_non_brazil_whatsapp(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:14155552671']})
		)
		client.get.return_value = LIST_EMPTY

		with pytest.raises(ContactNotFoundError):
			sender.get()

		assert client.get.call_count == 1

	def test_get_maps_flows_http_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = FlowsHTTPError(400, 'bad request')

		with pytest.raises(ContactSenderError, match='400'):
			sender.get()

	def test_get_maps_flows_network_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = FlowsNetworkError('network down')

		with pytest.raises(ContactSenderError, match='network down'):
			sender.get()

	def test_get_maps_flows_response_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = FlowsResponseError('unreadable body')

		with pytest.raises(ContactSenderError, match='unreadable body'):
			sender.get()

	def test_get_missing_urn_before_http(self):
		sender, client = _sender()
		with pytest.raises(ContactSenderConfigError):
			sender.get()
		client.get.assert_not_called()

	def test_get_unexpected_list_response(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = ['not', 'a', 'dict']

		with pytest.raises(ContactSenderError, match='Unexpected Flows contacts list response'):
			sender.get()

	def test_get_invalid_results_key(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = {'results': 'not-a-list'}

		with pytest.raises(ContactSenderError, match='Unexpected Flows contacts list response'):
			sender.get()

	def test_get_ambiguous_on_alternate_retry(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = [
			LIST_EMPTY,
			{'results': [CONTACT, CONTACT], 'next': None, 'previous': None},
		]

		with pytest.raises(ContactAmbiguousError):
			sender.get()


class TestContactSenderUpdate:
	def test_update_success_with_fields(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		updated = {**CONTACT, 'fields': {'email': 'leonardo.amaral@vtex.com'}}
		client.post.return_value = updated

		result = sender.update(fields={'email': 'leonardo.amaral@vtex.com'})

		assert result == updated
		client.post.assert_called_once_with(
			'/api/v2/contacts.json',
			params={'urn': 'whatsapp:5582999893640'},
			json={'fields': {'email': 'leonardo.amaral@vtex.com'}},
		)

	def test_update_with_name_kwarg(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		client.post.return_value = {**CONTACT, 'name': 'New Name'}

		sender.update(name='New Name')

		client.post.assert_called_once_with(
			'/api/v2/contacts.json',
			params={'urn': 'whatsapp:5582999893640'},
			json={'name': 'New Name'},
		)

	def test_update_hybrid_payload_kwargs_precedence(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		client.post.return_value = CONTACT

		sender.update({'name': 'From Dict'}, name='From Kwargs')

		client.post.assert_called_once_with(
			'/api/v2/contacts.json',
			params={'urn': 'whatsapp:5582999893640'},
			json={'name': 'From Kwargs'},
		)

	def test_update_empty_body_raises_validation_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)

		with pytest.raises(ContactValidationError):
			sender.update()

		client.get.assert_not_called()
		client.post.assert_not_called()

	def test_update_urns_in_body_raises_validation_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)

		with pytest.raises(ContactValidationError, match='urns'):
			sender.update(urns=['tel:+123'])

		client.get.assert_not_called()
		client.post.assert_not_called()

	def test_update_not_found_skips_post(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:14155552671']})
		)
		client.get.return_value = LIST_EMPTY

		with pytest.raises(ContactNotFoundError):
			sender.update(fields={'email': 'a@b.com'})

		client.post.assert_not_called()

	def test_update_uses_effective_urn_after_retry(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = [LIST_EMPTY, LIST_ONE]
		client.post.return_value = CONTACT

		sender.update(fields={'email': 'a@b.com'})

		client.post.assert_called_once_with(
			'/api/v2/contacts.json',
			params={'urn': 'whatsapp:558299893640'},
			json={'fields': {'email': 'a@b.com'}},
		)

	def test_update_explicit_urn_override(self):
		sender, client = _sender()
		client.get.return_value = LIST_ONE
		client.post.return_value = CONTACT

		sender.update({'fields': {'email': 'a@b.com'}}, urn='whatsapp:override')

		client.get.assert_called_with('/api/v2/contacts.json', params={'urn': 'whatsapp:override'})
		client.post.assert_called_once_with(
			'/api/v2/contacts.json',
			params={'urn': 'whatsapp:override'},
			json={'fields': {'email': 'a@b.com'}},
		)

	def test_update_maps_flows_http_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		client.post.side_effect = FlowsHTTPError(500, 'server error')

		with pytest.raises(ContactSenderError, match='500'):
			sender.update(fields={'email': 'a@b.com'})

	def test_update_maps_flows_network_error(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		client.post.side_effect = FlowsNetworkError('connection refused')

		with pytest.raises(ContactSenderError, match='connection refused'):
			sender.update(fields={'email': 'a@b.com'})

	def test_update_unexpected_post_response(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.return_value = LIST_ONE
		client.post.return_value = 'not-a-dict'

		with pytest.raises(ContactSenderError, match='Unexpected Flows contact update response'):
			sender.update(fields={'email': 'a@b.com'})


class TestContactSenderErrorHierarchy:
	def test_specific_errors_are_subclasses(self):
		assert issubclass(ContactSenderConfigError, ContactSenderError)
		assert issubclass(ContactNotFoundError, ContactSenderError)
		assert issubclass(ContactAmbiguousError, ContactSenderError)
		assert issubclass(ContactValidationError, ContactSenderError)

	def test_catch_all_contact_sender_error(self):
		with pytest.raises(ContactSenderError):
			raise ContactNotFoundError('missing')

	def test_flows_client_error_is_not_leaked_raw(self):
		sender, client = _sender(
			create_context(project=default_project(), contact={'urns': ['whatsapp:5582999893640']})
		)
		client.get.side_effect = FlowsHTTPError(404, 'not found')

		with pytest.raises(ContactSenderError) as exc_info:
			sender.get()

		assert not isinstance(exc_info.value, FlowsClientError)
