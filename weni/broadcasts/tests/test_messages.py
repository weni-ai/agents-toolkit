"""
Tests for broadcast message types.
"""

import pytest

from weni.broadcasts.messages import (
    Text,
    Attachment,
    QuickReply,
    ListMessage,
    ListItem,
    CTAMessage,
    Location,
    OrderDetails,
    OrderItem,
    Catalog,
)


class TestTextMessage:
    """Tests for Text message."""

    def test_format_message(self):
        """Test Text message formatting."""
        msg = Text(text="Hello, world!")
        payload = msg.format_message()

        assert payload["type"] == "text"
        assert payload["text"] == "Hello, world!"


class TestAttachmentMessage:
    """Tests for Attachment message."""

    def test_format_with_image(self):
        """Test Attachment with image."""
        msg = Attachment(text="Check this out", image="https://example.com/img.png")
        payload = msg.format_message()

        assert payload["type"] == "attachment"
        assert payload["text"] == "Check this out"
        assert "image/png:https://example.com/img.png" in payload["attachments"]

    def test_format_with_document(self):
        """Test Attachment with document."""
        msg = Attachment(document="https://example.com/doc.pdf")
        payload = msg.format_message()

        assert "application/pdf:https://example.com/doc.pdf" in payload["attachments"]

    def test_format_without_text(self):
        """Test Attachment without text."""
        msg = Attachment(image="https://example.com/img.png")
        payload = msg.format_message()

        assert "text" not in payload


class TestQuickReplyMessage:
    """Tests for QuickReply message."""

    def test_format_basic(self):
        """Test basic QuickReply."""
        msg = QuickReply(text="Choose one:", options=["Yes", "No"])
        payload = msg.format_message()

        assert payload["type"] == "quick_reply"
        assert payload["text"] == "Choose one:"
        assert payload["quick_replies"] == ["Yes", "No"]

    def test_format_with_header_footer(self):
        """Test QuickReply with header and footer."""
        msg = QuickReply(
            text="Choose one:",
            options=["A", "B"],
            header="Important",
            footer="Tap to select"
        )
        payload = msg.format_message()

        assert payload["header"]["text"] == "Important"
        assert payload["footer"] == "Tap to select"


class TestListMessage:
    """Tests for ListMessage."""

    def test_format_basic(self):
        """Test basic ListMessage."""
        msg = ListMessage(
            text="Select an option:",
            button_text="View",
            items=[
                ListItem(title="Option 1", description="First"),
                ListItem(title="Option 2", description="Second"),
            ]
        )
        payload = msg.format_message()

        assert payload["type"] == "list"
        assert payload["text"] == "Select an option:"
        assert payload["list_message"]["button_text"] == "View"
        assert len(payload["list_message"]["list_items"]) == 2
        assert payload["list_message"]["list_items"][0]["title"] == "Option 1"


class TestCTAMessage:
    """Tests for CTAMessage."""

    def test_format_basic(self):
        """Test basic CTAMessage."""
        msg = CTAMessage(
            text="Visit our website",
            url="https://example.com",
            display_text="Open"
        )
        payload = msg.format_message()

        assert payload["type"] == "cta_url"
        assert payload["cta_message"]["url"] == "https://example.com"
        assert payload["cta_message"]["display_text"] == "Open"


class TestLocationMessage:
    """Tests for Location message."""

    def test_format_basic(self):
        """Test basic Location."""
        msg = Location(text="Share your location")
        payload = msg.format_message()

        assert payload["type"] == "location"
        assert payload["text"] == "Share your location"
        assert payload["interactive_type"] == "location"


class TestOrderDetailsMessage:
    """Tests for OrderDetails message."""

    def test_format_basic(self):
        """Test basic OrderDetails."""
        msg = OrderDetails(
            text="Your order:",
            reference_id="ORDER-123",
            items=[
                OrderItem(retailer_id="SKU-1", name="Product A", value=1000, quantity=2)
            ],
            total_amount=2000,
            subtotal=2000,
            payment_type="pix"
        )
        payload = msg.format_message()

        assert payload["type"] == "order_details"
        assert payload["order_details"]["reference_id"] == "ORDER-123"
        assert payload["order_details"]["total_amount"] == 2000
        assert len(payload["order_details"]["order"]["items"]) == 1


class TestCatalogMessage:
    """Tests for Catalog message."""

    def test_format_basic(self):
        """Test basic Catalog."""
        msg = Catalog(text="Browse products")
        payload = msg.format_message()

        assert payload["type"] == "catalog"
        assert payload["text"] == "Browse products"

    def test_format_with_thumbnail(self):
        """Test Catalog with thumbnail."""
        msg = Catalog(text="Products", thumbnail_product_retailer_id="PROD-1")
        payload = msg.format_message()

        assert payload["thumbnail_product_retailer_id"] == "PROD-1"
