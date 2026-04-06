"""
Broadcast Message Types.

Message classes for building WhatsApp broadcast payloads.
Each message type knows how to format itself for the Flows API.

These are different from the Response components - these are for
sending messages during tool execution, not for formatting responses.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class Message(ABC):
    """
    Base class for all broadcast message types.

    Messages are used to build payloads for the WhatsApp Broadcasts API.
    Each message type implements `format_message()` to return the
    appropriate payload structure.
    """

    @abstractmethod
    def format_message(self) -> dict[str, Any]:
        """
        Format the message as a dictionary payload for the API.

        Returns:
            Dictionary with the message payload.
        """
        pass

    def _apply_header_footer(self, payload: dict[str, Any], header: str | None, footer: str | None) -> None:
        """
        Apply header and footer to a message payload.

        This helper method provides consistent formatting for header and footer
        fields across message types that support them (QuickReply, ListMessage,
        CTAMessage).

        Args:
            payload: The message payload dict to modify in-place.
            header: Optional header text. If provided, adds a header object
                   with type "text".
            footer: Optional footer text. If provided, adds as a simple string.
        """
        if header:
            payload["header"] = {"type": "text", "text": header}
        if footer:
            payload["footer"] = footer


@dataclass
class Text(Message):
    """
    Simple text message.

    Args:
        text: The message text content.

    Example:
        ```python
        msg = Text(text="Hello! How can I help you?")
        Broadcast.send(msg)
        ```
    """

    text: str

    def format_message(self) -> dict[str, Any]:
        return {
            "text": self.text,
        }


@dataclass
class QuickReply(Message):
    """
    Message with quick reply buttons.

    Args:
        text: The message text.
        options: List of quick reply button labels.
        header: Optional header text.
        footer: Optional footer text.

    Example:
        ```python
        msg = QuickReply(
            text="Do you want to continue?",
            options=["Yes", "No", "Maybe"]
        )
        Broadcast.send(msg)
        ```
    """

    text: str
    options: list[str] = field(default_factory=list)
    header: str | None = None
    footer: str | None = None

    def format_message(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "text": self.text,
            "quick_replies": self.options,
        }
        self._apply_header_footer(payload, self.header, self.footer)
        return payload


@dataclass
class WebChatProduct:
    """A product with full details for Weni WebChat catalog."""

    name: str
    price: str
    retailer_id: str
    seller_id: str
    currency: str = "BRL"
    description: str | None = None
    image: str | None = None
    sale_price: str | None = None
    product_url: str | None = None


@dataclass
class WebChatProductGroup:
    """A group of products under a category for Weni WebChat."""

    product: str
    product_retailer_info: list[WebChatProduct] = field(default_factory=list)


@dataclass
class WeniWebChatCatalog(Message):
    """
    Catalog message for Weni WebChat with full product details.

    Products can be passed as dicts — no need to import WebChatProductGroup/WebChatProduct.

    Example:
        ```python
        Broadcast(self).send(WeniWebChatCatalog(
            text="Here are our products",
            products=[{
                "product": "Shirts",
                "product_retailer_info": [
                    {"name": "Blue Shirt", "price": "149.90", "retailer_id": "85961", "seller_id": "1"},
                ],
            }],
        ))
        ```
    """

    text: str
    products: list[WebChatProductGroup] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.products = [
            WebChatProductGroup(
                product=group["product"],
                product_retailer_info=[
                    WebChatProduct(**product) for product in group.get("product_retailer_info", [])
                ],
            ) if isinstance(group, dict) else group
            for group in self.products
        ]
    action_button_text: str = "Comprar"
    send_catalog: bool = False
    header: str | None = None
    footer: str | None = None

    def format_message(self) -> dict[str, Any]:
        product_groups = []
        for group in self.products:
            items = []
            for item in group.product_retailer_info:
                product_dict: dict[str, Any] = {
                    "name": item.name,
                    "price": item.price,
                    "retailer_id": item.retailer_id,
                    "seller_id": item.seller_id,
                    "currency": item.currency,
                }
                if item.description:
                    product_dict["description"] = item.description
                if item.image:
                    product_dict["image"] = item.image
                if item.sale_price:
                    product_dict["sale_price"] = item.sale_price
                if item.product_url:
                    product_dict["product_url"] = item.product_url
                items.append(product_dict)
            product_groups.append({
                "product": group.product,
                "product_retailer_info": items,
            })

        payload: dict[str, Any] = {
            "text": self.text,
            "catalog_message": {
                "send_catalog": self.send_catalog,
                "products": product_groups,
                "action_button_text": self.action_button_text,
            },
        }
        self._apply_header_footer(payload, self.header, self.footer)
        return payload


@dataclass
class WhatsAppProductGroup:
    """A group of products by retailer IDs for WhatsApp catalog."""

    product: str
    product_retailer_ids: list[str] = field(default_factory=list)


@dataclass
class WhatsAppCatalog(Message):
    """
    Catalog message for WhatsApp with product retailer IDs.

    Products can be passed as dicts — no need to import WhatsAppProductGroup.

    Example:
        ```python
        Broadcast(self).send(WhatsAppCatalog(
            text="Here are our shirts",
            products=[
                {"product": "Workshirt Titan Coyote", "product_retailer_ids": ["12552#1#1", "12553#1#1"]},
            ],
        ))
        ```
    """

    text: str
    products: list[WhatsAppProductGroup] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.products = [
            WhatsAppProductGroup(**group) if isinstance(group, dict) else group
            for group in self.products
        ]
    action_button_text: str = "Comprar"
    send_catalog: bool = False
    header: str | None = None
    footer: str | None = None

    def format_message(self) -> dict[str, Any]:
        product_groups = []
        for group in self.products:
            product_groups.append({
                "product": group.product,
                "product_retailer_ids": group.product_retailer_ids,
            })

        payload: dict[str, Any] = {
            "text": self.text,
            "catalog_message": {
                "send_catalog": self.send_catalog,
                "products": product_groups,
                "action_button_text": self.action_button_text,
            },
        }
        self._apply_header_footer(payload, self.header, self.footer)
        return payload


@dataclass
class OrderItem:
    """A single item in a one-click payment order."""

    retailer_id: str
    name: str
    amount: int
    quantity: int = 1
    sale_amount: int | None = None


@dataclass
class OneClickPayment(Message):
    """
    One-click payment message with saved card details.

    Items can be passed as dicts — no need to import OrderItem.

    Example:
        ```python
        Broadcast(self).send(OneClickPayment(
            text="Use this card to pay?",
            reference_id="ORDER-123",
            last_four_digits="4242",
            credential_id="acc_001",
            total_amount=15000,
            items=[{"retailer_id": "SKU-1", "name": "Shirt", "amount": 15000}],
            subtotal=15000,
        ))
        ```
    """

    text: str
    reference_id: str
    last_four_digits: str
    credential_id: str
    total_amount: int
    items: list[OrderItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.items = [
            OrderItem(**item) if isinstance(item, dict) else item
            for item in self.items
        ]
    subtotal: int = 0
    tax_value: int = 0
    discount_value: int = 0
    shipping_value: int = 0

    def format_message(self) -> dict[str, Any]:
        order_items = []
        for item in self.items:
            item_dict: dict[str, Any] = {
                "retailer_id": item.retailer_id,
                "name": item.name,
                "amount": {"value": item.amount, "offset": 100},
                "quantity": item.quantity,
            }
            if item.sale_amount is not None:
                item_dict["sale_amount"] = {"value": item.sale_amount, "offset": 100}
            order_items.append(item_dict)

        order: dict[str, Any] = {
            "items": order_items,
            "subtotal": self.subtotal,
            "tax": {"description": "Impostos", "offset": 100, "value": self.tax_value},
            "discount": {"description": "Desconto", "offset": 100, "value": self.discount_value},
            "shipping": {"description": "Frete", "offset": 100, "value": self.shipping_value},
        }

        return {
            "text": self.text,
            "interaction_type": "order_details",
            "order_details": {
                "reference_id": self.reference_id,
                "type": "digital-goods",
                "payment_settings": {
                    "type": "offsite_card_pay",
                    "offsite_card_pay": {
                        "last_four_digits": str(self.last_four_digits),
                        "credential_id": str(self.credential_id),
                    },
                },
                "total_amount": self.total_amount,
                "order": order,
            },
        }


@dataclass
class WhatsAppFlows(Message):
    """
    WhatsApp Flows interactive message.

    Example:
        ```python
        Broadcast(self).send(WhatsAppFlows(
            text="You have a pending confirmation.",
            flow_id="1451561746318256",
            flow_cta="Confirm Now",
            flow_screen="COLLECT_DATA",
            flow_data={"order_value": "R$ 150,00"},
        ))
        ```
    """

    text: str
    flow_id: str
    flow_cta: str
    flow_screen: str
    flow_data: dict[str, Any] = field(default_factory=dict)
    flow_mode: str = "published"

    def format_message(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "interaction_type": "flow_msg",
            "flow_message": {
                "flow_id": self.flow_id,
                "flow_cta": self.flow_cta,
                "flow_mode": self.flow_mode,
                "flow_screen": self.flow_screen,
                "flow_data": self.flow_data,
            },
        }
