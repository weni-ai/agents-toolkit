"""Tests for Contact facade."""

from unittest.mock import MagicMock, patch

import pytest

from weni.contacts.contact import Contact
from weni.contacts.sender import ContactNotFoundError, ContactValidationError
from weni.contacts.tests.conftest import create_context, default_project


def tool_with_contact(contact: dict | None = None) -> MagicMock:
	"""Build a tool double whose context is a real Context, so merges actually happen."""
	mock_tool = MagicMock()
	mock_tool.context = create_context(project=default_project(), contact=contact or {})
	return mock_tool


class TestContactFacade:
	@patch('weni.contacts.sender.ContactSender')
	def test_get_delegates_to_sender(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.get.return_value = {'uuid': 'abc'}
		mock_sender_class.return_value = mock_sender

		mock_tool = MagicMock()
		mock_tool.context = create_context(project=default_project())

		result = Contact(mock_tool).get()

		mock_sender_class.assert_called_once_with(mock_tool.context)
		mock_sender.get.assert_called_once_with(urn=None)
		assert result == {'uuid': 'abc'}

	@patch('weni.contacts.sender.ContactSender')
	def test_get_forwards_urn_override(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender_class.return_value = mock_sender

		mock_tool = MagicMock()
		mock_tool.context = create_context(project=default_project())

		Contact(mock_tool).get(urn='whatsapp:override')

		mock_sender.get.assert_called_once_with(urn='whatsapp:override')

	@patch('weni.contacts.sender.ContactSender')
	def test_update_delegates_to_sender(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.update.return_value = {'uuid': 'abc'}
		mock_sender_class.return_value = mock_sender

		mock_tool = MagicMock()
		mock_tool.context = create_context(project=default_project())

		result = Contact(mock_tool).update({'fields': {'email': 'a@b.com'}}, urn='whatsapp:5582', name='Name')

		mock_sender.update.assert_called_once_with(
			payload={'fields': {'email': 'a@b.com'}},
			urn='whatsapp:5582',
			name='Name',
		)
		assert result == {'uuid': 'abc'}

	@patch('weni.contacts.sender.ContactSender')
	def test_propagates_sender_errors(self, mock_sender_class):
		mock_sender = MagicMock()
		mock_sender.get.side_effect = ContactNotFoundError('missing')
		mock_sender_class.return_value = mock_sender

		mock_tool = MagicMock()
		mock_tool.context = create_context(project=default_project())

		with pytest.raises(ContactNotFoundError, match='missing'):
			Contact(mock_tool).get()

	@patch('weni.contacts.sender.ContactSender')
	def test_lazy_imports_sender_module(self, mock_sender_class):
		mock_sender_class.return_value = MagicMock()

		mock_tool = MagicMock()
		mock_tool.context = create_context(project=default_project())

		Contact(mock_tool).get()

		mock_sender_class.assert_called_once_with(mock_tool.context)


class TestContactOperationLog:
	"""Operations are only logged once the Flows write has succeeded."""

	@patch.object(Contact, '_get_sender')
	def test_update_does_not_register_operation_when_sender_fails(self, mock_get_sender):
		mock_get_sender.return_value.update.side_effect = ContactValidationError('invalid')
		mock_tool = tool_with_contact({'fields': {'email': 'old@example.com'}})

		with pytest.raises(ContactValidationError, match='invalid'):
			Contact(mock_tool).update(fields={'email': 'new@example.com'})

		mock_tool._register_operation.assert_not_called()
		assert mock_tool.context.contact == {'fields': {'email': 'old@example.com'}}

	@patch.object(Contact, '_get_sender')
	def test_update_registers_merged_body_after_success(self, mock_get_sender):
		mock_get_sender.return_value.update.return_value = {'uuid': 'abc'}
		mock_tool = tool_with_contact()

		Contact(mock_tool).update({'fields': {'email': 'new@example.com'}}, name='Jane')

		mock_tool._register_operation.assert_called_once_with(
			'contacts_updated',
			{'fields': {'email': 'new@example.com'}, 'name': 'Jane'},
		)

	@patch.object(Contact, '_get_sender')
	def test_get_does_not_register_operation_when_sender_fails(self, mock_get_sender):
		mock_get_sender.return_value.get.side_effect = ContactNotFoundError('missing')
		mock_tool = tool_with_contact()

		with pytest.raises(ContactNotFoundError, match='missing'):
			Contact(mock_tool).get(urn='whatsapp:5582')

		mock_tool._register_operation.assert_not_called()

	@patch.object(Contact, '_get_sender')
	def test_get_registers_raw_urn_after_success(self, mock_get_sender):
		mock_get_sender.return_value.get.return_value = {'uuid': 'abc'}
		mock_tool = tool_with_contact()

		Contact(mock_tool).get(urn='whatsapp:5582')

		mock_tool._register_operation.assert_called_once_with('contacts_get', 'whatsapp:5582')


class TestContactContextRefresh:
	"""A successful update is reflected by the context for the rest of the execution."""

	@patch.object(Contact, '_get_sender')
	def test_update_refreshes_context_with_whitelisted_keys_only(self, mock_get_sender):
		mock_get_sender.return_value.update.return_value = {
			'uuid': 'contact-uuid',
			'modified_on': '2026-07-29T00:00:00Z',
			'blocked': False,
			'name': 'Jane',
			'language': 'por',
			'groups': [{'name': 'Leads'}],
			'urns': ['whatsapp:5582'],
			'fields': {'email': 'new@example.com'},
		}
		mock_tool = tool_with_contact({'name': 'John', 'fields': {'email': 'old@example.com', 'cpf': '123'}})

		Contact(mock_tool).update(fields={'email': 'new@example.com'})

		assert mock_tool.context.contact == {
			'name': 'Jane',
			'language': 'por',
			'groups': [{'name': 'Leads'}],
			'urns': ['whatsapp:5582'],
			'fields': {'email': 'new@example.com', 'cpf': '123'},
		}

	@patch.object(Contact, '_get_sender')
	def test_update_reflects_new_field_on_the_context_reference_held_by_execute(self, mock_get_sender):
		mock_get_sender.return_value.update.return_value = {'uuid': 'abc', 'fields': {'email': 'new@example.com'}}
		mock_tool = tool_with_contact({'fields': {'email': 'old@example.com'}})
		context = mock_tool.context

		Contact(mock_tool).update(fields={'email': 'new@example.com'})

		assert context.contact['fields']['email'] == 'new@example.com'

	@patch.object(Contact, '_get_sender')
	def test_update_contact_shorthand_refreshes_context(self, mock_get_sender):
		mock_get_sender.return_value.update.return_value = {'fields': {'email': 'new@example.com'}}
		mock_tool = tool_with_contact({'fields': {'email': 'old@example.com'}})

		result = Contact(mock_tool)._update_contact_compat({'fields': {'email': 'new@example.com'}})

		mock_get_sender.return_value.update.assert_called_once_with(
			payload={'fields': {'email': 'new@example.com'}},
			urn=None,
		)
		assert result == {'fields': {'email': 'new@example.com'}}
		assert mock_tool.context.contact['fields']['email'] == 'new@example.com'

	@patch.object(Contact, '_get_sender')
	def test_update_leaves_context_untouched_when_response_has_no_contact_attributes(self, mock_get_sender):
		mock_get_sender.return_value.update.return_value = {'uuid': 'abc', 'modified_on': '2026-07-29T00:00:00Z'}
		mock_tool = tool_with_contact({'fields': {'email': 'old@example.com'}})

		Contact(mock_tool).update(fields={'email': 'new@example.com'})

		assert mock_tool.context.contact == {'fields': {'email': 'old@example.com'}}
