import pytest
from weni.components import (
    Component,
    Text,
    Header,
    Footer,
    QuickReplies,
    ListMessage,
    CTAMessage,
    Location,
    OrderDetails,
    Attachments,
)


def test_get_format_example_method_cannot_be_overridden():
    """Test that get_format_example method cannot be overridden by child classes"""
    with pytest.raises(TypeError) as exc_info:

        class ChildComponent(Component):
            @classmethod
            def get_format_example(cls):  # type: ignore[misc]
                pass

    assert "Cannot override final method 'get_format_example'" in str(exc_info.value)


def test_get_format_example_method_can_be_called():
    """Test that get_format_example method can be called from both parent and child classes"""

    class ValidChildComponent(Component):
        pass

    # Should not raise any exceptions
    Component.get_format_example()
    ValidChildComponent.get_format_example()


def test_empty_component_format_example():
    """Test getting format example from a component with no format example set"""

    class EmptyComponent(Component):
        pass

    result = EmptyComponent.get_format_example()
    assert result == {}


def test_component_with_format_example():
    """Test getting format example from a component with a format example set"""

    class CustomComponent(Component):
        _format_example = {"custom": "example"}

    result = CustomComponent.get_format_example()
    assert result == {"custom": "example"}


def test_text_component_format_example():
    """Test getting format example from Text component"""
    result = Text.get_format_example()
    assert "text" in result
    assert isinstance(result["text"], str)


def test_header_component_format_example():
    """Test getting format example from Header component"""
    result = Header.get_format_example()
    assert "header" in result
    assert "type" in result["header"]
    assert "text" in result["header"]


def test_footer_component_format_example():
    """Test getting format example from Footer component"""
    result = Footer.get_format_example()
    assert "footer" in result
    assert isinstance(result["footer"], str)


def test_attachments_component_format_example():
    """Test getting format example from Attachments component"""
    result = Attachments.get_format_example()
    assert "attachments" in result
    assert isinstance(result["attachments"], list)


def test_quick_replies_component_format_example():
    """Test getting format example from QuickReplies component"""
    result = QuickReplies.get_format_example()
    assert "quick_replies" in result
    assert isinstance(result["quick_replies"], list)


def test_list_message_component_format_example():
    """Test getting format example from ListMessage component"""
    result = ListMessage.get_format_example()
    assert "interactive_type" in result
    assert result["interactive_type"] == "list"
    assert "list_message" in result
    assert "button_text" in result["list_message"]
    assert "list_items" in result["list_message"]


def test_cta_message_component_format_example():
    """Test getting format example from CTAMessage component"""
    result = CTAMessage.get_format_example()
    assert "interactive_type" in result
    assert result["interactive_type"] == "cta_url"
    assert "cta_message" in result
    assert "url" in result["cta_message"]
    assert "display_text" in result["cta_message"]


def test_location_component_format_example():
    """Test getting format example from Location component"""
    result = Location.get_format_example()
    assert "interactive_type" in result
    assert result["interactive_type"] == "location"


def test_order_details_component_format_example():
    """Test getting format example from OrderDetails component"""
    result = OrderDetails.get_format_example()
    assert "interactive_type" in result
    assert result["interactive_type"] == "order_details"
    assert "order_details" in result
    assert "reference_id" in result["order_details"]
    assert "payment_settings" in result["order_details"]
    assert "total_amount" in result["order_details"]
    assert "order" in result["order_details"]
