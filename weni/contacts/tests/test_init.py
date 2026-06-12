"""Tests for weni.contacts public exports."""

from weni import contacts


def test_public_exports():
	assert set(contacts.__all__) == {
		'Contact',
		'ContactAmbiguousError',
		'ContactNotFoundError',
		'ContactSender',
		'ContactSenderConfigError',
		'ContactSenderError',
		'ContactValidationError',
	}

	for name in contacts.__all__:
		assert hasattr(contacts, name)
