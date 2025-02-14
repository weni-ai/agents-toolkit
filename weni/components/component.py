import json
from typing import final, Any, ClassVar


class Component:
    """Base class for all components."""

    _description: ClassVar[str] = ""
    _format: ClassVar[dict[str, Any]] = {}
    _example: ClassVar[dict[str, Any]] = {}
    _rules: ClassVar[list[str]] = []
    _required_components: ClassVar[list[type["Component"]]] = []
    _allowed_components: ClassVar[list[type["Component"]]] = []

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Prevents subclasses from overriding the parse method."""
        super().__init_subclass__(**kwargs)
        if "parse" in cls.__dict__:
            raise TypeError("Cannot override final method 'parse'")

    @final
    @classmethod
    def parse(cls):
        """Parse the component and return a string representation of it with its rules alongside its required and allowed components."""

        required_components = (
            [component.parse() for component in cls._required_components] if cls._required_components else []
        )
        allowed_components = (
            [component.parse() for component in cls._allowed_components] if cls._allowed_components else []
        )
        rules = cls._rules if cls._rules else []

        # mount result, adding only if it's not empty
        result_parts = []
        if cls._description:
            result_parts.append(f"[{cls.__name__}] is: {cls._description}")
        if rules:
            result_parts.append(f"[{cls.__name__}] Component Rules: {rules}")
        if required_components:
            components_str = "[" + "\n".join(required_components) + "]"
            result_parts.append(f"[{cls.__name__}] Required components: {components_str}")
        if allowed_components:
            components_str = "[" + "\n".join(allowed_components) + "]"
            result_parts.append(f"[{cls.__name__}] Allowed components: {components_str}")
        if cls._format:
            result_parts.append(f"[{cls.__name__}] Format: {json.dumps(cls._format, indent=None)}")
        if cls._example:
            result_parts.append(f"[{cls.__name__}] Example: {json.dumps(cls._example, indent=None)}")

        result = "\n".join(filter(None, result_parts))
        return result


class Text(Component):
    _description = "A text message"
    _format = {"msg": {"text": "<text>"}}
    _example = {"msg": {"text": "Hello, how can I help you today?"}}


class Header(Component):
    _description = "A header message"
    _format = {"msg": {"header": {"type": "text", "text": "<text>"}}}
    _example = {"msg": {"header": {"type": "text", "text": "Important Message"}}}
    _rules = [
        "Cannot be used alone, must alongside another component that allows it.",
    ]


class Footer(Component):
    _description = "A footer message"
    _format = {"msg": {"footer": {"type": "text", "text": "<text>"}}}
    _example = {"msg": {"footer": {"type": "text", "text": "Powered by Weni"}}}
    _rules = [
        "Cannot be used alone, must be used alongside another component that allows it.",
    ]


class Attachments(Component):
    _description = "A list of file links, images, audio, video, documents"
    _format = {"msg": {"text": "<text>", "attachments": ["<mime_type>:<url>"]}}
    _example = {"msg": {"text": "Check this image", "attachments": ["image/png:https://example.com/image.png"]}}
    _allowed_components = [Text]


class QuickReplies(Component):
    _description = "A list of quick replies"
    _format = {"msg": {"text": "<text>", "quick_replies": ["<reply>"]}}
    _example = {"msg": {"text": "Would you like to proceed?", "quick_replies": ["Yes", "No"]}}
    _rules = [
        "Can not have both Header and Attachments at the same time.",
    ]
    _required_components = [Text]
    _allowed_components = [Header, Footer, Attachments]


class ListMessage(Component):
    _description = "A list of items, used like a menu"
    _format = {
        "msg": {
            "text": "<text>",
            "interactive_type": "list",
            "list_message": {
                "button_text": "<button_text>",
                "list_items": [{"title": "<title>", "description": "<description>", "uuid": "<random_uuid>"}],
            },
        }
    }
    _example = {
        "msg": {
            "text": "Choose an option",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "Item 1", "description": "Description 1", "uuid": "123e4567-e89b-12d3-a456-426614174000"}
                ],
            },
        }
    }
    _rules = [
        "Can not have both Header and Attachments at the same time.",
        "The interactive_type must be 'list'.",
    ]
    _required_components = [Text]
    _allowed_components = [Header, Footer, Attachments]


class CTAMessage(Component):
    _description = "A call to action message"
    _format = {
        "msg": {
            "text": "<text>",
            "interactive_type": "cta_url",
            "cta_message": {"url": "<url>", "display_text": "<display_text>"},
        }
    }
    _example = {
        "msg": {
            "text": "Choose an option",
            "interactive_type": "cta_url",
            "cta_message": {"url": "https://example.com", "display_text": "View details"},
        }
    }
    _rules = [
        "The interactive_type must be 'cta_url'.",
    ]
    _required_components = [Text]
    _allowed_components = [Header, Footer]


class Location(Component):
    _description = "A location request message"
    _format = {"msg": {"text": "<text>", "interactive_type": "location"}}
    _example = {"msg": {"text": "Share your location", "interactive_type": "location"}}
    _rules = [
        "The interactive_type must be 'location'.",
    ]
    _required_components = [Text]


class OrderDetails(Component):
    _description = "An order details message"
    _format = {
        "msg": {
            "text": "<text>",
            "interactive_type": "order_details",
            "order_details": {
                "reference_id": "<reference_id>",
                "payment_settings": {
                    "type": "<order_type>",
                    "payment_link": "<payment_link>",
                    "pix_config": {
                        "key": "<pix_key>",
                        "key_type": "<pix_key_type>",
                        "merchant_name": "<merchant_name>",
                        "code": "<pix_code>",
                    },
                },
                "total_amount": "<total_amount>",
                "order": {
                    "items": [
                        {
                            "retailer_id": "<product_retailer_id>",
                            "name": "<product_name>",
                            "amount": {
                                "value": "<product_value>",
                                "offset": 100,
                            },
                            "quantity": 1,
                            "sale_amount": {"value": "<product_sale_amount>", "offset": 100},
                        }
                    ],
                    "subtotal": "<subtotal>",
                    "tax": {"description": "<tax_description>", "value": "<tax_value>", "offset": 100},
                    "shipping": {"description": "<shipping_description>", "value": "<shipping_value>", "offset": 100},
                    "discount": {"description": "<discount_description>", "value": "<discount_value>", "offset": 100},
                },
            },
        }
    }
    _example = {
        "msg": {
            "text": "Order #123",
            "interactive_type": "order_details",
            "order_details": {
                "reference_id": "ORDER123",
                "payment_settings": {
                    "type": "PIX",
                    "payment_link": "https://payment.example.com/123",
                    "pix_config": {
                        "key": "pix@example.com",
                        "key_type": "email",
                        "merchant_name": "Example Store",
                        "code": "00020126580014br.gov.bcb.pix0136pix@example.com",
                    },
                },
                "total_amount": 15000,
                "order": {
                    "items": [
                        {
                            "retailer_id": "PROD123",
                            "name": "Example Product",
                            "amount": {"value": 10000, "offset": 100},
                            "quantity": 1,
                            "sale_amount": {"value": 10000, "offset": 100},
                        }
                    ],
                    "subtotal": 10000,
                    "tax": {"description": "Tax", "value": 2000, "offset": 100},
                    "shipping": {"description": "Standard Shipping", "value": 3000, "offset": 100},
                    "discount": {"description": "Welcome Discount", "value": 0, "offset": 100},
                },
            },
        }
    }
    _rules = [
        "The interactive_type must be 'order_details'.",
    ]
    _required_components = [Text]
    _allowed_components = [Attachments, Footer]
