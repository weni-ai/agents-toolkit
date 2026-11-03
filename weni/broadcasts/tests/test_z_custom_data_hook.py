"""
Runs after the other broadcast tests.

Subclasses created inside those tests stay registered, so this check sees the
production message types and the edge-case subclasses together.
"""

from weni.broadcasts.tests.test_message_contract import assert_every_format_message_is_wrapped


def test_every_message_subclass_created_during_the_suite_is_wrapped():
    assert_every_format_message_is_wrapped()
