from weni.responses import (
    TextResponse,
    AttachmentResponse,
    QuickReplyResponse,
    ListMessageResponse,
    CTAMessageResponse,
    OrderDetailsResponse,
    LocationResponse,
    HeaderType,
)


def test_text_response():
    """Test TextResponse with different configurations"""
    # Basic text response
    result, format = TextResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_attachment_response():
    """Test AttachmentResponse with different configurations"""
    # Basic attachment response
    result, format = AttachmentResponse(data={})
    assert result == {}
    assert format == {"msg": {"attachments": ["image/png:https://example.com/image.png"]}}

    # Attachment with footer
    result, format = AttachmentResponse(data={}, text=True, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "attachments": ["image/png:https://example.com/image.png"],
            "footer": "Powered by Weni",
        }
    }


def test_quick_reply_response():
    """Test QuickReplyResponse with different configurations"""
    # Basic quick reply
    result, format = QuickReplyResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?", "quick_replies": ["Yes", "No"]}}

    # Quick reply with header
    result, format = QuickReplyResponse(data={}, header_type=HeaderType.TEXT, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
            "footer": "Powered by Weni",
        }
    }

    # Quick reply with attachments
    result, format = QuickReplyResponse(data={}, header_type=HeaderType.ATTACHMENTS, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "attachments": ["image/png:https://example.com/image.png"],
            "footer": "Powered by Weni",
        }
    }


def test_list_message_response():
    """Test ListMessageResponse with different configurations"""
    # Basic list message
    result, format = ListMessageResponse(data={})
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
        }
    }

    # List message with header
    result, format = ListMessageResponse(data={}, header_type=HeaderType.TEXT, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
            "header": {"type": "text", "text": "Important Message"},
            "footer": "Powered by Weni",
        }
    }

    # List message with attachments
    result, format = ListMessageResponse(data={}, header_type=HeaderType.ATTACHMENTS, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
            "attachments": ["image/png:https://example.com/image.png"],
            "footer": "Powered by Weni",
        }
    }


def test_cta_message_response():
    """Test CTAMessageResponse with different configurations"""
    # Basic CTA message
    result, format = CTAMessageResponse(data={})
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "cta_url",
            "cta_message": {"url": "https://example.com", "display_text": "Go to website"},
        }
    }

    # CTA message with header
    result, format = CTAMessageResponse(data={}, header=True, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "cta_url",
            "cta_message": {"url": "https://example.com", "display_text": "Go to website"},
            "header": {"type": "text", "text": "Important Message"},
            "footer": "Powered by Weni",
        }
    }


def test_order_details_response():
    """Test OrderDetailsResponse with different configurations"""
    base_format = {
        "msg": {
            "text": "Hello, how can I help you today?",
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

    # Basic order details
    result, format = OrderDetailsResponse(data={})
    assert result == {}
    assert format == base_format

    # Order details with attachments
    result, format = OrderDetailsResponse(data={}, attachments=True, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            **base_format["msg"],
            "attachments": ["image/png:https://example.com/image.png"],
            "footer": "Powered by Weni",
        }
    }


def test_location_response():
    """Test LocationResponse"""
    # Basic location response
    result, format = LocationResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?", "interactive_type": "location"}}


def test_response_type_combinations():
    """Test all valid HeaderType combinations for each response"""
    # QuickReply supports all types
    result, format = QuickReplyResponse(data={}, header_type=HeaderType.NONE)
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?", "quick_replies": ["Yes", "No"]}}

    result, format = QuickReplyResponse(data={}, header_type=HeaderType.TEXT)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
        }
    }

    result, format = QuickReplyResponse(data={}, header_type=HeaderType.ATTACHMENTS)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "attachments": ["image/png:https://example.com/image.png"],
        }
    }

    # ListMessage supports all types
    result, format = ListMessageResponse(data={}, header_type=HeaderType.NONE)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
        }
    }

    result, format = ListMessageResponse(data={}, header_type=HeaderType.TEXT)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "header": {"type": "text", "text": "Important Message"},
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
        }
    }

    result, format = ListMessageResponse(data={}, header_type=HeaderType.ATTACHMENTS)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "attachments": ["image/png:https://example.com/image.png"],
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
        }
    }


def test_footer_combinations():
    """Test footer combinations with different responses"""
    result, format = AttachmentResponse(data={}, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "attachments": ["image/png:https://example.com/image.png"],
            "footer": "Powered by Weni",
        }
    }

    result, format = QuickReplyResponse(data={}, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "footer": "Powered by Weni",
        }
    }

    result, format = ListMessageResponse(data={}, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
            "footer": "Powered by Weni",
        }
    }

    result, format = CTAMessageResponse(data={}, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "cta_url",
            "cta_message": {"url": "https://example.com", "display_text": "Go to website"},
            "footer": "Powered by Weni",
        }
    }

    result, format = OrderDetailsResponse(data={}, footer=True)
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
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
            "footer": "Powered by Weni",
        }
    }


def test_required_components():
    """Test that required components are always present"""
    # Text is required for most responses, except for AttachmentResponse

    result, format = TextResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    result, format = QuickReplyResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?", "quick_replies": ["Yes", "No"]}}

    result, format = ListMessageResponse(data={})
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "list",
            "list_message": {
                "button_text": "Select an option",
                "list_items": [
                    {"title": "First option title", "description": "First option description", "uuid": "<random_uuid>"}
                ],
            },
        }
    }

    result, format = CTAMessageResponse(data={})
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "interactive_type": "cta_url",
            "cta_message": {"url": "https://example.com", "display_text": "Go to website"},
        }
    }

    result, format = OrderDetailsResponse(data={})
    assert result == {}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
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

    result, format = LocationResponse(data={})
    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?", "interactive_type": "location"}}


def test_response_data_handling():
    """Test that response data is handled correctly"""
    test_data = {"key": "value", "nested": {"test": True}}

    result, _ = TextResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = AttachmentResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = QuickReplyResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = ListMessageResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = CTAMessageResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = OrderDetailsResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}

    result, _ = LocationResponse(data=test_data)
    assert result == {"key": "value", "nested": {"test": True}}
