"""
Guards around the custom_data injection hook.

A new message type, or a format_message that bypasses Message.__init_subclass__,
should fail here instead of shipping without custom_data.
"""

import weni.broadcasts as broadcasts
import weni.broadcasts.messages as messages_module
from weni.broadcasts.messages import (
    Message,
    OneClickPayment,
    PixPayment,
    QuickReply,
    Text,
    WeniWebChatCatalog,
    WhatsAppCarousel,
    WhatsAppCatalog,
    WhatsAppFlows,
)
from weni.broadcasts.tests.golden_payloads import GOLDEN_CASES

# Closed list of message types that ship in this package.
# Adding a class to messages.py without a golden payload and a custom_data
# case fails the tests below.
KNOWN_MESSAGE_TYPES = {
    Text,
    QuickReply,
    WeniWebChatCatalog,
    WhatsAppCatalog,
    OneClickPayment,
    WhatsAppFlows,
    WhatsAppCarousel,
    PixPayment,
}

_CONTRACT_HINT = (
    "Update KNOWN_MESSAGE_TYPES and add a GoldenCase in golden_payloads.py "
    "(minimal and full payloads, with and without custom_data)."
)


def _walk_subclasses(cls: type) -> list[type]:
    found: list[type] = []
    for subclass in cls.__subclasses__():
        found.append(subclass)
        found.extend(_walk_subclasses(subclass))
    return found


def _messages_defined_in_module() -> set[type]:
    defined = set()
    for obj in vars(messages_module).values():
        if isinstance(obj, type) and issubclass(obj, Message) and obj is not Message:
            defined.add(obj)
    return defined


class TestMessageTypeContract:
    def test_module_matches_the_known_list(self):
        defined = _messages_defined_in_module()
        new = defined - KNOWN_MESSAGE_TYPES
        missing = KNOWN_MESSAGE_TYPES - defined

        assert not new and not missing, f"Message types changed. New: {new or 'none'}. Missing: {missing or 'none'}. {_CONTRACT_HINT}"

    def test_known_types_are_exported(self):
        exported = {getattr(broadcasts, name) for name in broadcasts.__all__}
        missing = KNOWN_MESSAGE_TYPES - exported

        assert not missing, f"Export these message types in weni.broadcasts.__all__: {missing}. {_CONTRACT_HINT}"

    def test_golden_payloads_cover_every_known_type(self):
        covered = {case.message_cls for case in GOLDEN_CASES}

        assert covered == KNOWN_MESSAGE_TYPES, f"Golden payloads are out of date. {_CONTRACT_HINT}"


class TestCustomDataHookEdges:
    def test_reassigning_format_message_after_creation_drops_injection(self):
        """Documents the hook's limit: it runs at class creation, not on later assignment."""
        original = Text.format_message

        def bare(self):
            return {"text": self.text}

        try:
            Text.format_message = bare  # type: ignore[method-assign]
            payload = Text(text="x", custom_data={"a": 1}).format_message()
            assert payload == {"text": "x"}
            assert getattr(Text.format_message, "_custom_data_injected", False) is False
        finally:
            Text.format_message = original  # type: ignore[method-assign]

        restored = Text(text="x", custom_data={"a": 1}).format_message()
        assert restored["custom_data"] == {"a": 1}

    def test_mixin_providing_format_message_is_wrapped(self):
        class PayloadMixin:
            def format_message(self):
                self.created = {"source": "mixin"}
                return self.created

        class Mixed(PayloadMixin, Message):
            def __init__(self, custom_data=None):
                self.custom_data = custom_data

        plain = Mixed()
        assert plain.format_message() is plain.created
        assert "custom_data" not in plain.created

        rich = Mixed(custom_data={"k": "v"})
        assert rich.format_message() == {"source": "mixin", "custom_data": {"k": "v"}}

    def test_super_chain_injects_without_duplicating_fields(self):
        class Extra(Text):
            def format_message(self):  # type: ignore[override]
                payload = super().format_message()
                payload["extra"] = "yes"
                return payload

        payload = Extra(text="hi", custom_data={"a": 1}).format_message()

        assert payload == {"text": "hi", "custom_data": {"a": 1}, "extra": "yes"}

    def test_external_subclass_with_its_own_init(self):
        class External(Message):
            def __init__(self, text, custom_data=None):
                self.text = text
                self.custom_data = custom_data

            def format_message(self):
                return {"text": self.text}

        assert External("hi").format_message() == {"text": "hi"}
        assert External("hi", custom_data={"a": 1}).format_message() == {
            "text": "hi",
            "custom_data": {"a": 1},
        }

    def test_unusual_payload_is_returned_unchanged_without_custom_data(self):
        class Odd(Message):
            def __init__(self):
                self.custom_data = None

            def format_message(self):
                self.payload = {"weird": object()}
                return self.payload

        odd = Odd()
        assert odd.format_message() is odd.payload

    def test_every_subclass_format_message_is_wrapped(self):
        assert_every_format_message_is_wrapped()


def assert_every_format_message_is_wrapped() -> None:
    for cls in _walk_subclasses(Message):
        method = getattr(cls, "format_message")
        assert getattr(method, "_custom_data_injected", False), (
            f"{cls.__module__}.{cls.__name__}.format_message is not wrapped by "
            "Message.__init_subclass__. Define format_message in the class body. "
            "Assigning it after the class is created skips the hook."
        )
