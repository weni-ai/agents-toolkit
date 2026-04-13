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
    OneClickPayment,
    OrderItem,
    PixPayment,
    WhatsAppFlows,
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


class TestOneClickPayment:
    def test_format_basic(self):
        msg = OneClickPayment(
            text="Use this card to pay?",
            reference_id="ORDER-123",
            last_four_digits="4242",
            credential_id="acc_001",
            total_amount=15000,
            items=[OrderItem(retailer_id="SKU-1", name="Shirt", amount=15000)],
            subtotal=15000,
        )
        payload = msg.format_message()

        assert payload["text"] == "Use this card to pay?"
        assert payload["interaction_type"] == "order_details"

        details = payload["order_details"]
        assert details["reference_id"] == "ORDER-123"
        assert details["type"] == "digital-goods"
        assert details["total_amount"] == 15000

        payment = details["payment_settings"]
        assert payment["type"] == "offsite_card_pay"
        assert payment["offsite_card_pay"]["last_four_digits"] == "4242"
        assert payment["offsite_card_pay"]["credential_id"] == "acc_001"

        order = details["order"]
        assert len(order["items"]) == 1
        assert order["items"][0]["retailer_id"] == "SKU-1"
        assert order["items"][0]["name"] == "Shirt"
        assert order["items"][0]["amount"] == {"value": 15000, "offset": 100}
        assert order["items"][0]["quantity"] == 1
        assert order["subtotal"] == 15000
        assert order["tax"]["value"] == 0
        assert order["discount"]["value"] == 0
        assert order["shipping"]["value"] == 0

    def test_format_with_all_fields(self):
        msg = OneClickPayment(
            text="Confirm payment?",
            reference_id="REF-456",
            last_four_digits="1234",
            credential_id="acc_002",
            total_amount=25000,
            items=[
                OrderItem(retailer_id="SKU-1", name="Product A", amount=10000, quantity=2),
                OrderItem(retailer_id="SKU-2", name="Product B", amount=5000, sale_amount=4000),
            ],
            subtotal=25000,
            tax_value=500,
            discount_value=1000,
            shipping_value=800,
        )
        payload = msg.format_message()

        order = payload["order_details"]["order"]
        assert len(order["items"]) == 2
        assert order["items"][0]["quantity"] == 2
        assert "sale_amount" not in order["items"][0]
        assert order["items"][1]["sale_amount"] == {"value": 4000, "offset": 100}
        assert order["tax"]["value"] == 500
        assert order["discount"]["value"] == 1000
        assert order["shipping"]["value"] == 800


class TestWhatsAppFlows:
    def test_format_basic(self):
        msg = WhatsAppFlows(
            text="You have a pending confirmation.",
            flow_id="1451561746318256",
            flow_cta="Confirm Now",
            flow_screen="COLLECT_DATA",
        )
        payload = msg.format_message()

        assert payload["text"] == "You have a pending confirmation."
        assert payload["interaction_type"] == "flow_msg"

        flow = payload["flow_message"]
        assert flow["flow_id"] == "1451561746318256"
        assert flow["flow_cta"] == "Confirm Now"
        assert flow["flow_mode"] == "published"
        assert flow["flow_screen"] == "COLLECT_DATA"
        assert flow["flow_token"] is None
        assert flow["flow_data"] == {}

    def test_format_with_token(self):
        msg = WhatsAppFlows(
            text="Confirm",
            flow_id="123",
            flow_cta="Go",
            flow_screen="SCREEN",
            flow_token="tok_abc123",
        )
        payload = msg.format_message()
        assert payload["flow_message"]["flow_token"] == "tok_abc123"

    def test_format_with_data(self):
        msg = WhatsAppFlows(
            text="Confirm your order",
            flow_id="123456",
            flow_cta="Confirm",
            flow_screen="ORDER_SCREEN",
            flow_data={"order_value": "R$ 150,00", "card_last_four": "1234"},
            flow_mode="draft",
        )
        payload = msg.format_message()

        flow = payload["flow_message"]
        assert flow["flow_data"] == {"order_value": "R$ 150,00", "card_last_four": "1234"}
        assert flow["flow_mode"] == "draft"


class TestDictShorthand:
    """Tests that all message types accept dicts instead of dataclass imports."""

    def test_webchat_catalog_with_dicts(self):
        msg = WeniWebChatCatalog(
            text="Products",
            products=[{
                "product": "Shirts",
                "product_retailer_info": [
                    {"name": "Blue Shirt", "price": "149.90", "retailer_id": "85961", "seller_id": "1"},
                ],
            }],
        )
        payload = msg.format_message()

        assert payload["catalog_message"]["products"][0]["product"] == "Shirts"
        assert payload["catalog_message"]["products"][0]["product_retailer_info"][0]["name"] == "Blue Shirt"

    def test_whatsapp_catalog_with_dicts(self):
        msg = WhatsAppCatalog(
            text="Shirts",
            products=[
                {"product": "Titan Coyote", "product_retailer_ids": ["12552#1#1"]},
            ],
        )
        payload = msg.format_message()

        assert payload["catalog_message"]["products"][0]["product"] == "Titan Coyote"
        assert payload["catalog_message"]["products"][0]["product_retailer_ids"] == ["12552#1#1"]

    def test_one_click_payment_with_dicts(self):
        msg = OneClickPayment(
            text="Pay now?",
            reference_id="ORDER-1",
            last_four_digits="4242",
            credential_id="acc_1",
            total_amount=10000,
            items=[{"retailer_id": "SKU-1", "name": "Shirt", "amount": 10000}],
            subtotal=10000,
        )
        payload = msg.format_message()

        assert payload["order_details"]["order"]["items"][0]["retailer_id"] == "SKU-1"
        assert payload["order_details"]["order"]["items"][0]["amount"] == {"value": 10000, "offset": 100}


class TestPixPayment:
    def test_format_basic(self):
        msg = PixPayment(
            text="Copy the PIX code to pay.",
            reference_id="ORDER-001",
            pix_key="7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
            pix_key_type="EVP",
            merchant_name="MY STORE",
            pix_code="00020126580014br.gov.bcb.pix...",
            total_amount=34990,
            items=[{"retailer_id": "31245#1", "name": "Nike Air Max", "amount": 24990}],
            subtotal=29990,
            discount_value=1500,
            shipping_value=6500,
        )
        payload = msg.format_message()

        assert payload["text"] == "Copy the PIX code to pay."
        assert payload["interaction_type"] == "order_details"
        assert "footer" not in payload

        details = payload["order_details"]
        assert details["reference_id"] == "ORDER-001"
        assert details["total_amount"] == 34990

        pix = details["payment_settings"]["pix_config"]
        assert pix["key"] == "7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a"
        assert pix["key_type"] == "EVP"
        assert pix["merchant_name"] == "MY STORE"
        assert pix["code"] == "00020126580014br.gov.bcb.pix..."

        order = details["order"]
        assert len(order["items"]) == 1
        assert order["items"][0]["retailer_id"] == "31245#1"
        assert order["subtotal"] == 29990
        assert order["discount"]["value"] == 1500
        assert order["shipping"]["value"] == 6500

    def test_format_with_footer(self):
        msg = PixPayment(
            text="Pay now",
            reference_id="REF-1",
            pix_key="key",
            pix_key_type="CPF",
            merchant_name="Store",
            pix_code="code",
            total_amount=1000,
            items=[{"retailer_id": "1", "name": "Item", "amount": 1000}],
            subtotal=1000,
            footer="Thanks for your purchase",
        )
        payload = msg.format_message()

        assert payload["footer"] == "Thanks for your purchase"

    def test_format_with_multiple_items(self):
        msg = PixPayment(
            text="Pay",
            reference_id="REF-2",
            pix_key="key",
            pix_key_type="EVP",
            merchant_name="Store",
            pix_code="code",
            total_amount=5000,
            items=[
                {"retailer_id": "A", "name": "Product A", "amount": 2500, "quantity": 1},
                {"retailer_id": "B", "name": "Product B", "amount": 2500, "quantity": 2},
            ],
            subtotal=5000,
        )
        payload = msg.format_message()

        items = payload["order_details"]["order"]["items"]
        assert len(items) == 2
        assert items[0]["quantity"] == 1
        assert items[1]["quantity"] == 2
