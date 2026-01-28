"""
Broadcast Message Types.

Message classes for building WhatsApp broadcast payloads.
Each message type knows how to format itself for the Flows API.

These are different from the Response components - these are for
sending messages during tool execution, not for formatting responses.
"""

import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


def _get_mime_type(url: str, default_mime: str) -> str:
    """
    Infer MIME type from URL file extension.

    Args:
        url: The URL to extract MIME type from.
        default_mime: Default MIME type if detection fails.

    Returns:
        The inferred MIME type or the default.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            return mime_type
    except Exception:
        pass
    return default_mime


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
            "type": "text",
            "text": self.text,
        }


@dataclass
class Attachment(Message):
    """
    Message with attachment (image, document, video, audio).

    Args:
        text: Optional caption text.
        image: URL of image attachment.
        document: URL of document attachment.
        video: URL of video attachment.
        audio: URL of audio attachment.

    Example:
        ```python
        msg = Attachment(
            text="Here's the image you requested",
            image="https://example.com/image.png"
        )
        Broadcast.send(msg)
        ```
    """

    text: str | None = None
    image: str | None = None
    document: str | None = None
    video: str | None = None
    audio: str | None = None

    def format_message(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": "attachment"}

        if self.text:
            payload["text"] = self.text

        attachments = []
        if self.image:
            mime = _get_mime_type(self.image, "image/png")
            attachments.append(f"{mime}:{self.image}")
        if self.document:
            mime = _get_mime_type(self.document, "application/pdf")
            attachments.append(f"{mime}:{self.document}")
        if self.video:
            mime = _get_mime_type(self.video, "video/mp4")
            attachments.append(f"{mime}:{self.video}")
        if self.audio:
            mime = _get_mime_type(self.audio, "audio/mpeg")
            attachments.append(f"{mime}:{self.audio}")

        if attachments:
            payload["attachments"] = attachments

        return payload


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
            "type": "quick_reply",
            "text": self.text,
            "quick_replies": self.options,
        }

        if self.header:
            payload["header"] = {"type": "text", "text": self.header}

        if self.footer:
            payload["footer"] = self.footer

        return payload


@dataclass
class ListItem:
    """Single item in a list message."""

    title: str
    description: str | None = None
    uuid: str | None = None


@dataclass
class ListMessage(Message):
    """
    Interactive list message with selectable items.

    Args:
        text: The message text.
        button_text: Text for the list button.
        items: List of ListItem objects.
        header: Optional header text.
        footer: Optional footer text.

    Example:
        ```python
        msg = ListMessage(
            text="Select an option:",
            button_text="View options",
            items=[
                ListItem(title="Option 1", description="First option"),
                ListItem(title="Option 2", description="Second option"),
            ]
        )
        Broadcast.send(msg)
        ```
    """

    text: str
    button_text: str
    items: list[ListItem] = field(default_factory=list)
    header: str | None = None
    footer: str | None = None

    def format_message(self) -> dict[str, Any]:
        list_items = []
        for item in self.items:
            item_dict: dict[str, Any] = {"title": item.title}
            if item.description:
                item_dict["description"] = item.description
            if item.uuid:
                item_dict["uuid"] = item.uuid
            list_items.append(item_dict)

        payload: dict[str, Any] = {
            "type": "list",
            "text": self.text,
            "interactive_type": "list",
            "list_message": {
                "button_text": self.button_text,
                "list_items": list_items,
            },
        }

        if self.header:
            payload["header"] = {"type": "text", "text": self.header}

        if self.footer:
            payload["footer"] = self.footer

        return payload


@dataclass
class CTAMessage(Message):
    """
    Call-to-Action message with a URL button.

    Args:
        text: The message text.
        url: The URL to link to.
        display_text: Text to display on the button.
        header: Optional header text.
        footer: Optional footer text.

    Example:
        ```python
        msg = CTAMessage(
            text="Visit our website for more info",
            url="https://example.com",
            display_text="Open Website"
        )
        Broadcast.send(msg)
        ```
    """

    text: str
    url: str
    display_text: str
    header: str | None = None
    footer: str | None = None

    def format_message(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "cta_url",
            "text": self.text,
            "interactive_type": "cta_url",
            "cta_message": {
                "url": self.url,
                "display_text": self.display_text,
            },
        }

        if self.header:
            payload["header"] = {"type": "text", "text": self.header}

        if self.footer:
            payload["footer"] = self.footer

        return payload


@dataclass
class Location(Message):
    """
    Location request message.

    Args:
        text: The message text asking for location.

    Example:
        ```python
        msg = Location(text="Please share your location")
        Broadcast.send(msg)
        ```
    """

    text: str

    def format_message(self) -> dict[str, Any]:
        return {
            "type": "location",
            "text": self.text,
            "interactive_type": "location",
        }


@dataclass
class OrderItem:
    """Single item in an order."""

    retailer_id: str
    name: str
    value: int
    quantity: int = 1
    sale_amount: int | None = None


@dataclass
class OrderDetails(Message):
    """
    Order details message with payment information.

    Args:
        text: The message text.
        reference_id: Order reference ID.
        items: List of OrderItem objects.
        total_amount: Total order amount.
        subtotal: Order subtotal.
        tax_value: Tax amount (optional).
        tax_description: Tax description (optional).
        shipping_value: Shipping amount (optional).
        shipping_description: Shipping description (optional).
        discount_value: Discount amount (optional).
        discount_description: Discount description (optional).
        payment_type: Payment type.
        payment_link: Payment link URL (optional).
        pix_key: PIX key (optional).
        pix_key_type: PIX key type (optional).
        merchant_name: Merchant name (optional).
        pix_code: PIX code (optional).

    Example:
        ```python
        msg = OrderDetails(
            text="Your order details:",
            reference_id="ORDER-123",
            items=[OrderItem(retailer_id="SKU-1", name="Product", value=1000, quantity=2)],
            total_amount=2000,
            subtotal=2000,
            payment_type="pix"
        )
        Broadcast.send(msg)
        ```
    """

    text: str
    reference_id: str
    items: list[OrderItem] = field(default_factory=list)
    total_amount: int = 0
    subtotal: int = 0
    tax_value: int | None = None
    tax_description: str | None = None
    shipping_value: int | None = None
    shipping_description: str | None = None
    discount_value: int | None = None
    discount_description: str | None = None
    payment_type: str = "pix"
    payment_link: str | None = None
    pix_key: str | None = None
    pix_key_type: str | None = None
    merchant_name: str | None = None
    pix_code: str | None = None

    def format_message(self) -> dict[str, Any]:
        order_items = []
        for item in self.items:
            item_dict: dict[str, Any] = {
                "retailer_id": item.retailer_id,
                "name": item.name,
                "amount": {"value": item.value, "offset": 100},
                "quantity": item.quantity,
            }
            if item.sale_amount is not None:
                item_dict["sale_amount"] = {"value": item.sale_amount, "offset": 100}
            order_items.append(item_dict)

        order: dict[str, Any] = {
            "items": order_items,
            "subtotal": self.subtotal,
        }

        if self.tax_value is not None:
            order["tax"] = {
                "description": self.tax_description or "Tax",
                "value": self.tax_value,
                "offset": 100,
            }

        if self.shipping_value is not None:
            order["shipping"] = {
                "description": self.shipping_description or "Shipping",
                "value": self.shipping_value,
                "offset": 100,
            }

        if self.discount_value is not None:
            order["discount"] = {
                "description": self.discount_description or "Discount",
                "value": self.discount_value,
                "offset": 100,
            }

        payment_settings: dict[str, Any] = {"type": self.payment_type}

        if self.payment_link:
            payment_settings["payment_link"] = self.payment_link

        if self.pix_key:
            payment_settings["pix_config"] = {
                "key": self.pix_key,
                "key_type": self.pix_key_type or "cpf",
                "merchant_name": self.merchant_name or "",
                "code": self.pix_code or "",
            }

        return {
            "type": "order_details",
            "text": self.text,
            "interactive_type": "order_details",
            "order_details": {
                "reference_id": self.reference_id,
                "payment_settings": payment_settings,
                "total_amount": self.total_amount,
                "order": order,
            },
        }


@dataclass
class Catalog(Message):
    """
    Catalog message for product browsing.

    Args:
        text: The message text.
        thumbnail_product_retailer_id: Product ID for the thumbnail.

    Example:
        ```python
        msg = Catalog(
            text="Browse our products",
            thumbnail_product_retailer_id="PRODUCT-123"
        )
        Broadcast.send(msg)
        ```
    """

    text: str
    thumbnail_product_retailer_id: str | None = None

    def format_message(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "catalog",
            "text": self.text,
            "interactive_type": "catalog",
        }

        if self.thumbnail_product_retailer_id:
            payload["thumbnail_product_retailer_id"] = self.thumbnail_product_retailer_id

        return payload
