"""
Tests for broadcast message types.
"""

from weni.broadcasts.messages import (
    Text,
    QuickReply,
    WeniWebChatCatalog,
    WebChatProduct,
    WebChatProductGroup,
    WhatsAppCatalog,
    WhatsAppProductGroup,
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


class TestWeniWebChatCatalog:
    def test_format_basic(self):
        msg = WeniWebChatCatalog(
            text="Here are our products",
            products=[
                WebChatProductGroup(
                    product="Shirts",
                    product_retailer_info=[
                        WebChatProduct(
                            name="Blue Shirt",
                            price="149.90",
                            retailer_id="85961",
                            seller_id="1",
                        ),
                    ],
                ),
            ],
        )
        payload = msg.format_message()

        assert payload["text"] == "Here are our products"
        assert payload["catalog_message"]["send_catalog"] is False
        assert payload["catalog_message"]["action_button_text"] == "Comprar"
        assert len(payload["catalog_message"]["products"]) == 1

        product_group = payload["catalog_message"]["products"][0]
        assert product_group["product"] == "Shirts"
        assert len(product_group["product_retailer_info"]) == 1

        item = product_group["product_retailer_info"][0]
        assert item["name"] == "Blue Shirt"
        assert item["price"] == "149.90"
        assert item["retailer_id"] == "85961"
        assert item["seller_id"] == "1"
        assert item["currency"] == "BRL"
        assert "description" not in item
        assert "image" not in item
        assert "sale_price" not in item

    def test_format_with_all_fields(self):
        msg = WeniWebChatCatalog(
            text="Products",
            header="Catalog Header",
            footer="Footer text",
            products=[
                WebChatProductGroup(
                    product="Camisas",
                    product_retailer_info=[
                        WebChatProduct(
                            name="Camisa Xadrez",
                            price="149.90",
                            retailer_id="85961",
                            seller_id="1",
                            description="A melhor camisa",
                            image="https://example.com/img.png",
                            sale_price="329.00",
                        ),
                    ],
                ),
            ],
        )
        payload = msg.format_message()

        assert payload["header"]["type"] == "text"
        assert payload["header"]["text"] == "Catalog Header"
        assert payload["footer"] == "Footer text"

        item = payload["catalog_message"]["products"][0]["product_retailer_info"][0]
        assert item["description"] == "A melhor camisa"
        assert item["image"] == "https://example.com/img.png"
        assert item["sale_price"] == "329.00"


class TestWhatsAppCatalog:
    def test_format_basic(self):
        msg = WhatsAppCatalog(
            text="Here are our shirts",
            products=[
                WhatsAppProductGroup(
                    product="Workshirt Titan Coyote",
                    product_retailer_ids=["12552#1#1", "12553#1#1"],
                ),
            ],
        )
        payload = msg.format_message()

        assert payload["text"] == "Here are our shirts"
        assert payload["catalog_message"]["send_catalog"] is False
        assert payload["catalog_message"]["action_button_text"] == "Comprar"
        assert len(payload["catalog_message"]["products"]) == 1

        group = payload["catalog_message"]["products"][0]
        assert group["product"] == "Workshirt Titan Coyote"
        assert group["product_retailer_ids"] == ["12552#1#1", "12553#1#1"]

    def test_format_with_header_footer(self):
        msg = WhatsAppCatalog(
            text="Shirts",
            header="Collection",
            footer="All UV protected",
            products=[
                WhatsAppProductGroup(
                    product="Titan Coyote",
                    product_retailer_ids=["12552#1#1"],
                ),
                WhatsAppProductGroup(
                    product="Titan Verde",
                    product_retailer_ids=["14040#1#1"],
                ),
            ],
            action_button_text="Buy now",
        )
        payload = msg.format_message()

        assert payload["header"]["text"] == "Collection"
        assert payload["footer"] == "All UV protected"
        assert payload["catalog_message"]["action_button_text"] == "Buy now"
        assert len(payload["catalog_message"]["products"]) == 2
