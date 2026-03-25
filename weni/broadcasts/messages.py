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


@dataclass
class WebChatProductGroup:
    """A group of products under a category for Weni WebChat."""

    product: str
    product_retailer_info: list[WebChatProduct] = field(default_factory=list)


@dataclass
class WeniWebChatCatalog(Message):
    """
    Catalog message for Weni WebChat with full product details.

    Example:
        ```python
        Broadcast(self).send(WeniWebChatCatalog(
            text="Here are our products",
            products=[
                WebChatProductGroup(
                    product="Shirts",
                    product_retailer_info=[
                        WebChatProduct(name="Blue Shirt", price="149.90", retailer_id="85961", seller_id="1"),
                    ]
                )
            ],
        ))
        ```
    """

    text: str
    products: list[WebChatProductGroup] = field(default_factory=list)
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

    Example:
        ```python
        Broadcast(self).send(WhatsAppCatalog(
            text="Here are our shirts",
            products=[
                WhatsAppProductGroup(
                    product="Workshirt Titan Coyote",
                    product_retailer_ids=["12552#1#1", "12553#1#1"],
                ),
            ],
        ))
        ```
    """

    text: str
    products: list[WhatsAppProductGroup] = field(default_factory=list)
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
