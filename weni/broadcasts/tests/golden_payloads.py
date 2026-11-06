"""
Frozen payloads for the broadcast message types.

These dicts are the exact output of format_message() before custom_data existed.
Tests compare against them so a change to an existing payload fails loudly.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True)
class GoldenCase:
    message_cls: type[Message]
    build_min: Callable[..., Message]
    expected_min: dict[str, Any]
    build_full: Callable[..., Message]
    expected_full: dict[str, Any]

    @property
    def name(self) -> str:
        return self.message_cls.__name__


def _with_custom_data(custom_data: dict[str, Any] | None) -> dict[str, Any]:
    if custom_data is None:
        return {}
    return {"custom_data": custom_data}


def _text_min(custom_data=None):
    return Text(text="Hello", **_with_custom_data(custom_data))


def _text_full(custom_data=None):
    return Text(text="Hello! How can I help you?", **_with_custom_data(custom_data))


def _quick_reply_min(custom_data=None):
    return QuickReply(text="Choose one:", options=["Yes", "No"], **_with_custom_data(custom_data))


def _quick_reply_full(custom_data=None):
    return QuickReply(
        text="Choose one:",
        options=["A", "B"],
        header="Important",
        footer="Tap to select",
        **_with_custom_data(custom_data),
    )


def _webchat_min(custom_data=None):
    return WeniWebChatCatalog(
        text="Products",
        products=[
            {
                "product": "Shirts",
                "product_retailer_info": [
                    {"name": "Blue Shirt", "price": "149.90", "retailer_id": "85961", "seller_id": "1"},
                ],
            }
        ],
        **_with_custom_data(custom_data),
    )


def _webchat_full(custom_data=None):
    return WeniWebChatCatalog(
        text="Here are our products",
        products=[
            {
                "product": "Shirts",
                "product_retailer_info": [
                    {
                        "name": "Blue Shirt",
                        "price": "149.90",
                        "retailer_id": "85961",
                        "seller_id": "1",
                        "currency": "USD",
                        "description": "Cotton",
                        "image": "https://cdn.example/img.jpg",
                        "sale_price": "99.90",
                        "product_url": "https://store.example/blue",
                    }
                ],
            }
        ],
        action_button_text="Buy",
        send_catalog=True,
        header="Featured",
        footer="Tap a product",
        **_with_custom_data(custom_data),
    )


def _whatsapp_catalog_min(custom_data=None):
    return WhatsAppCatalog(
        text="Shirts",
        products=[{"product": "Titan Coyote", "product_retailer_ids": ["12552#1#1"]}],
        **_with_custom_data(custom_data),
    )


def _whatsapp_catalog_full(custom_data=None):
    return WhatsAppCatalog(
        text="Here are our shirts",
        products=[{"product": "Workshirt Titan Coyote", "product_retailer_ids": ["12552#1#1", "12553#1#1"]}],
        action_button_text="Buy",
        send_catalog=True,
        header="Shirts",
        footer="Browse all items",
        **_with_custom_data(custom_data),
    )


def _one_click_min(custom_data=None):
    return OneClickPayment(
        text="Pay now?",
        reference_id="ORDER-1",
        last_four_digits="4242",
        credential_id="acc_1",
        total_amount=10000,
        items=[{"retailer_id": "SKU-1", "name": "Shirt", "amount": 10000}],
        subtotal=10000,
        **_with_custom_data(custom_data),
    )


def _one_click_full(custom_data=None):
    return OneClickPayment(
        text="Use this card to pay?",
        reference_id="ORDER-123",
        last_four_digits="4242",
        credential_id="acc_001",
        total_amount=15000,
        items=[
            {"retailer_id": "SKU-1", "name": "Shirt", "amount": 10000, "quantity": 2},
            {"retailer_id": "SKU-2", "name": "Socks", "amount": 5000, "quantity": 1, "sale_amount": 4000},
        ],
        subtotal=25000,
        tax_value=500,
        discount_value=1000,
        shipping_value=800,
        **_with_custom_data(custom_data),
    )


def _flows_min(custom_data=None):
    return WhatsAppFlows(text="Confirm", flow_id="123", flow_cta="Go", flow_screen="SCREEN", **_with_custom_data(custom_data))


def _flows_full(custom_data=None):
    return WhatsAppFlows(
        text="You have a pending confirmation.",
        flow_id="1451561746318256",
        flow_cta="Confirm Now",
        flow_screen="COLLECT_DATA",
        flow_token="tok_abc123",
        flow_data={"order_value": "R$ 150,00"},
        flow_mode="draft",
        **_with_custom_data(custom_data),
    )


def _carousel_min(custom_data=None):
    return WhatsAppCarousel(
        text="Hello",
        attachments=["image/jpg:https://cdn.example/img.png"],
        carousel=[{"body": "Card", "buttons": [{"button_id": "opt-1", "title": "Choose"}]}],
        **_with_custom_data(custom_data),
    )


def _carousel_full(custom_data=None):
    return WhatsAppCarousel(
        text="Check out our shirts",
        attachments=["image/jpg:https://cdn.example/a.jpg", "image/jpg:https://cdn.example/b.jpg"],
        carousel=[
            {
                "body": "Slide one",
                "buttons": [{"sub_type": "quick_reply", "parameters": {"id": "camisa-preta", "title": "Gostei"}}],
            },
            {"body": "Slide two", "buttons": [{"button_id": "camisa-azul", "title": "Gostei"}]},
        ],
        **_with_custom_data(custom_data),
    )


def _pix_min(custom_data=None):
    return PixPayment(
        text="Pay",
        reference_id="REF-1",
        pix_key="key",
        pix_key_type="CPF",
        merchant_name="Store",
        pix_code="code",
        total_amount=1000,
        items=[{"retailer_id": "1", "name": "Item", "amount": 1000}],
        subtotal=1000,
        **_with_custom_data(custom_data),
    )


def _pix_full(custom_data=None):
    return PixPayment(
        text="Copy the PIX code to pay.",
        reference_id="ORDER-001",
        pix_key="7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
        pix_key_type="EVP",
        merchant_name="MY STORE",
        pix_code="00020126580014br.gov.bcb.pix...",
        total_amount=34990,
        items=[{"retailer_id": "31245#1", "name": "Nike Air Max", "amount": 24990, "sale_amount": 20000}],
        subtotal=29990,
        tax_value=100,
        discount_value=1500,
        shipping_value=6500,
        footer="Thanks",
        **_with_custom_data(custom_data),
    )


_ORDER_MIN = {
    "items": [
        {"retailer_id": "SKU-1", "name": "Shirt", "amount": {"value": 10000, "offset": 100}, "quantity": 1},
    ],
    "subtotal": 10000,
    "tax": {"description": "Impostos", "offset": 100, "value": 0},
    "discount": {"description": "Desconto", "offset": 100, "value": 0},
    "shipping": {"description": "Frete", "offset": 100, "value": 0},
}

_ORDER_FULL = {
    "items": [
        {"retailer_id": "SKU-1", "name": "Shirt", "amount": {"value": 10000, "offset": 100}, "quantity": 2},
        {
            "retailer_id": "SKU-2",
            "name": "Socks",
            "amount": {"value": 5000, "offset": 100},
            "quantity": 1,
            "sale_amount": {"value": 4000, "offset": 100},
        },
    ],
    "subtotal": 25000,
    "tax": {"description": "Impostos", "offset": 100, "value": 500},
    "discount": {"description": "Desconto", "offset": 100, "value": 1000},
    "shipping": {"description": "Frete", "offset": 100, "value": 800},
}

_PIX_ORDER_MIN = {
    "items": [{"retailer_id": "1", "name": "Item", "amount": {"value": 1000, "offset": 100}, "quantity": 1}],
    "subtotal": 1000,
    "tax": {"description": "Impostos", "offset": 100, "value": 0},
    "discount": {"description": "Desconto", "offset": 100, "value": 0},
    "shipping": {"description": "Frete", "offset": 100, "value": 0},
}

_PIX_ORDER_FULL = {
    "items": [
        {
            "retailer_id": "31245#1",
            "name": "Nike Air Max",
            "amount": {"value": 24990, "offset": 100},
            "quantity": 1,
            "sale_amount": {"value": 20000, "offset": 100},
        }
    ],
    "subtotal": 29990,
    "tax": {"description": "Impostos", "offset": 100, "value": 100},
    "discount": {"description": "Desconto", "offset": 100, "value": 1500},
    "shipping": {"description": "Frete", "offset": 100, "value": 6500},
}


GOLDEN_CASES: list[GoldenCase] = [
    GoldenCase(
        Text,
        _text_min,
        {"text": "Hello"},
        _text_full,
        {"text": "Hello! How can I help you?"},
    ),
    GoldenCase(
        QuickReply,
        _quick_reply_min,
        {"text": "Choose one:", "quick_replies": ["Yes", "No"]},
        _quick_reply_full,
        {
            "text": "Choose one:",
            "quick_replies": ["A", "B"],
            "header": {"type": "text", "text": "Important"},
            "footer": "Tap to select",
        },
    ),
    GoldenCase(
        WeniWebChatCatalog,
        _webchat_min,
        {
            "text": "Products",
            "catalog_message": {
                "send_catalog": False,
                "products": [
                    {
                        "product": "Shirts",
                        "product_retailer_info": [
                            {
                                "name": "Blue Shirt",
                                "price": "149.90",
                                "retailer_id": "85961",
                                "seller_id": "1",
                                "currency": "BRL",
                            }
                        ],
                    }
                ],
                "action_button_text": "Comprar",
            },
        },
        _webchat_full,
        {
            "text": "Here are our products",
            "catalog_message": {
                "send_catalog": True,
                "products": [
                    {
                        "product": "Shirts",
                        "product_retailer_info": [
                            {
                                "name": "Blue Shirt",
                                "price": "149.90",
                                "retailer_id": "85961",
                                "seller_id": "1",
                                "currency": "USD",
                                "description": "Cotton",
                                "image": "https://cdn.example/img.jpg",
                                "sale_price": "99.90",
                                "product_url": "https://store.example/blue",
                            }
                        ],
                    }
                ],
                "action_button_text": "Buy",
            },
            "header": {"type": "text", "text": "Featured"},
            "footer": "Tap a product",
        },
    ),
    GoldenCase(
        WhatsAppCatalog,
        _whatsapp_catalog_min,
        {
            "text": "Shirts",
            "catalog_message": {
                "send_catalog": False,
                "products": [{"product": "Titan Coyote", "product_retailer_ids": ["12552#1#1"]}],
                "action_button_text": "Comprar",
            },
        },
        _whatsapp_catalog_full,
        {
            "text": "Here are our shirts",
            "catalog_message": {
                "send_catalog": True,
                "products": [
                    {"product": "Workshirt Titan Coyote", "product_retailer_ids": ["12552#1#1", "12553#1#1"]}
                ],
                "action_button_text": "Buy",
            },
            "header": {"type": "text", "text": "Shirts"},
            "footer": "Browse all items",
        },
    ),
    GoldenCase(
        OneClickPayment,
        _one_click_min,
        {
            "text": "Pay now?",
            "interaction_type": "order_details",
            "order_details": {
                "reference_id": "ORDER-1",
                "type": "digital-goods",
                "payment_settings": {
                    "type": "offsite_card_pay",
                    "offsite_card_pay": {"last_four_digits": "4242", "credential_id": "acc_1"},
                },
                "total_amount": 10000,
                "order": _ORDER_MIN,
            },
        },
        _one_click_full,
        {
            "text": "Use this card to pay?",
            "interaction_type": "order_details",
            "order_details": {
                "reference_id": "ORDER-123",
                "type": "digital-goods",
                "payment_settings": {
                    "type": "offsite_card_pay",
                    "offsite_card_pay": {"last_four_digits": "4242", "credential_id": "acc_001"},
                },
                "total_amount": 15000,
                "order": _ORDER_FULL,
            },
        },
    ),
    GoldenCase(
        WhatsAppFlows,
        _flows_min,
        {
            "text": "Confirm",
            "interaction_type": "flow_msg",
            "flow_message": {
                "flow_id": "123",
                "flow_cta": "Go",
                "flow_mode": "published",
                "flow_screen": "SCREEN",
                "flow_token": None,
                "flow_data": {},
            },
        },
        _flows_full,
        {
            "text": "You have a pending confirmation.",
            "interaction_type": "flow_msg",
            "flow_message": {
                "flow_id": "1451561746318256",
                "flow_cta": "Confirm Now",
                "flow_mode": "draft",
                "flow_screen": "COLLECT_DATA",
                "flow_token": "tok_abc123",
                "flow_data": {"order_value": "R$ 150,00"},
            },
        },
    ),
    GoldenCase(
        WhatsAppCarousel,
        _carousel_min,
        {
            "text": "Hello",
            "interaction_type": "carousel",
            "attachments": ["image/jpg:https://cdn.example/img.png"],
            "carousel": [
                {"body": "Card", "buttons": [{"sub_type": "quick_reply", "parameters": {"id": "opt-1", "title": "Choose"}}]}
            ],
        },
        _carousel_full,
        {
            "text": "Check out our shirts",
            "interaction_type": "carousel",
            "attachments": ["image/jpg:https://cdn.example/a.jpg", "image/jpg:https://cdn.example/b.jpg"],
            "carousel": [
                {
                    "body": "Slide one",
                    "buttons": [{"sub_type": "quick_reply", "parameters": {"id": "camisa-preta", "title": "Gostei"}}],
                },
                {
                    "body": "Slide two",
                    "buttons": [{"sub_type": "quick_reply", "parameters": {"id": "camisa-azul", "title": "Gostei"}}],
                },
            ],
        },
    ),
    GoldenCase(
        PixPayment,
        _pix_min,
        {
            "text": "Pay",
            "interaction_type": "order_details",
            "order_details": {
                "reference_id": "REF-1",
                "payment_settings": {
                    "type": "digital-goods",
                    "pix_config": {"key": "key", "key_type": "CPF", "merchant_name": "Store", "code": "code"},
                },
                "total_amount": 1000,
                "order": _PIX_ORDER_MIN,
            },
        },
        _pix_full,
        {
            "text": "Copy the PIX code to pay.",
            "interaction_type": "order_details",
            "order_details": {
                "reference_id": "ORDER-001",
                "payment_settings": {
                    "type": "digital-goods",
                    "pix_config": {
                        "key": "7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
                        "key_type": "EVP",
                        "merchant_name": "MY STORE",
                        "code": "00020126580014br.gov.bcb.pix...",
                    },
                },
                "total_amount": 34990,
                "order": _PIX_ORDER_FULL,
            },
            "footer": "Thanks",
        },
    ),
]
