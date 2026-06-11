"""Tests for Contact facade."""

from unittest.mock import MagicMock, patch

import pytest

from weni.contacts.contact import Contact
from weni.contacts.sender import ContactNotFoundError
from weni.contacts.tests.conftest import create_context, default_project


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
