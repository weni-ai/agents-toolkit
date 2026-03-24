from typing import final, Any, ClassVar


class Component:
    """
    Base class for all components.

    Components define the structure and rules for different types of elements
    that can be used to display tool responses. Component attributes are
    immutable class variables.

    Class Attributes:
        _format_example (ClassVar[dict]): Expected JSON format for the component
    """

    _format_example: ClassVar[dict[str, Any]] = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Prevents subclasses from overriding the parse and get_format_example methods."""
        super().__init_subclass__(**kwargs)
        if "get_format_example" in cls.__dict__:
            raise TypeError("Cannot override final method 'get_format_example'")

    @final
    @classmethod
    def get_format_example(cls) -> dict[str, Any]:
        """Get the format example for the component."""
        return cls._format_example


class Text(Component):
    _format_example = {"text": "Hello, how can I help you today?"}


class Header(Component):
    _format_example = {"header": {"type": "text", "text": "Important Message"}}


class Footer(Component):
    _format_example = {"footer": "Powered by Weni"}


class Attachments(Component):
    _format_example = {"attachments": ["image/png:https://example.com/image.png"]}


class QuickReplies(Component):
    _format_example = {"quick_replies": ["Yes", "No"]}


class ListMessage(Component):
    _format_example = {
        "interactive_type": "list",
        "list_message": {
            "button_text": "Select an option",
            "list_items": [
                {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
            ],
        },
    }


class CTAMessage(Component):
    _format_example = {
        "interactive_type": "cta_url",
        "cta_message": {"url": "https://example.com", "display_text": "Go to website"},
    }


class Location(Component):
    _format_example = {"interactive_type": "location"}


class OrderDetails(Component):
    _format_example = {
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
