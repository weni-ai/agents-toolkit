"""
Tests for broadcast message types.
"""

from weni.broadcasts.messages import (
    Catalog,
    Text,
    QuickReply,
)

class TestTextMessage:
    """Tests for Text message."""

    def test_format_message(self):
        """Test Text message formatting."""
        msg = Text(text="Hello, world!")
        payload = msg.format_message()

        assert payload["text"] == "Hello, world!"
        assert "type" not in payload


class TestQuickReplyMessage:
    """Tests for QuickReply message."""

    def test_format_basic(self):
        """Test basic QuickReply."""
        msg = QuickReply(text="Choose one:", options=["Yes", "No"])
        payload = msg.format_message()

        assert payload["text"] == "Choose one:"
        assert payload["quick_replies"] == ["Yes", "No"]
        assert "type" not in payload

    def test_format_with_header_footer(self):
        """Test QuickReply with header and footer."""
        msg = QuickReply(text="Choose one:", options=["A", "B"], header="Important", footer="Tap to select")
        payload = msg.format_message()

        assert payload["header"]["text"] == "Important"
        assert payload["footer"] == "Tap to select"


class TestCatalogMessage:
    """Tests for Catalog message."""

    def test_format_basic(self):
        """Test basic Catalog."""
        msg = Catalog(text="Browse our products")
        payload = msg.format_message()

        assert payload["text"] == "Browse our products"
        assert payload["interaction_type"] == "catalog"
        assert "thumbnail_product_retailer_id" not in payload

    def test_format_with_thumbnail(self):
        """Test Catalog with thumbnail product."""
        msg = Catalog(text="Browse our products", thumbnail_product_retailer_id="PRODUCT-123")
        payload = msg.format_message()

        assert payload["text"] == "Browse our products"
        assert payload["interaction_type"] == "catalog"
        assert payload["thumbnail_product_retailer_id"] == "PRODUCT-123"
