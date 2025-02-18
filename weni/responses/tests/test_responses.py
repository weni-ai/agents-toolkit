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
from weni.components import (
    Text,
    Header,
    Footer,
    Attachments,
    QuickReplies,
    ListMessage,
    CTAMessage,
    Location,
    OrderDetails,
)


def test_text_response():
    """Test TextResponse with different configurations"""
    # Basic text response
    response = TextResponse(data={})
    assert response._components == [Text]


def test_attachment_response():
    """Test AttachmentResponse with different configurations"""
    # Basic attachment response
    response = AttachmentResponse(data={})
    assert set(response._components) == {Attachments}

    # Attachment with footer
    response = AttachmentResponse(data={}, text=True, footer=True)
    assert set(response._components) == {Text, Attachments, Footer}


def test_quick_reply_response():
    """Test QuickReplyResponse with different configurations"""
    # Basic quick reply
    response = QuickReplyResponse(data={})
    assert set(response._components) == {Text, QuickReplies}

    # Quick reply with header
    response = QuickReplyResponse(data={}, header_type=HeaderType.TEXT, footer=True)
    assert set(response._components) == {Text, QuickReplies, Header, Footer}

    # Quick reply with attachments
    response = QuickReplyResponse(data={}, header_type=HeaderType.ATTACHMENTS, footer=True)
    assert set(response._components) == {Text, QuickReplies, Attachments, Footer}


def test_list_message_response():
    """Test ListMessageResponse with different configurations"""
    # Basic list message
    response = ListMessageResponse(data={})
    assert set(response._components) == {Text, ListMessage}

    # List message with header
    response = ListMessageResponse(data={}, header_type=HeaderType.TEXT, footer=True)
    assert set(response._components) == {Text, ListMessage, Header, Footer}


def test_cta_message_response():
    """Test CTAMessageResponse with different configurations"""
    # Basic CTA message
    response = CTAMessageResponse(data={})
    assert set(response._components) == {Text, CTAMessage}

    # CTA message with header
    response = CTAMessageResponse(data={}, header=True, footer=True)
    assert set(response._components) == {Text, CTAMessage, Header, Footer}


def test_data_immutability():
    """Test that response data remains immutable"""
    data = {"key": "value"}
    response = TextResponse(data=data)

    # Original data should not be modified
    assert response._data == {"key": "value"}
    assert data == {"key": "value"}


def test_components_immutability():
    """Test that response components remain immutable"""
    response = QuickReplyResponse(data={}, header_type=HeaderType.TEXT)
    original_components = response._components.copy()

    # Try to modify components (this should create a new list)
    modified = response._components + [Footer]

    # Original components should remain unchanged
    assert response._components == original_components
    assert modified != response._components


def test_order_details_response():
    """Test OrderDetailsResponse with different configurations"""
    # Basic order details
    response = OrderDetailsResponse(data={})
    assert set(response._components) == {Text, OrderDetails}

    # Order details with attachments
    response = OrderDetailsResponse(data={}, attachments=True, footer=True)
    assert set(response._components) == {Text, OrderDetails, Attachments, Footer}


def test_location_response():
    """Test LocationResponse"""
    # Basic location response
    response = LocationResponse(data={})
    assert set(response._components) == {Text, Location}


def test_response_type_combinations():
    """Test all valid HeaderType combinations for each response"""
    # QuickReply supports all types
    response = QuickReplyResponse(data={}, header_type=HeaderType.NONE)
    assert set(response._components) == {Text, QuickReplies}

    response = QuickReplyResponse(data={}, header_type=HeaderType.TEXT)
    assert set(response._components) == {Text, QuickReplies, Header}

    response = QuickReplyResponse(data={}, header_type=HeaderType.ATTACHMENTS)
    assert set(response._components) == {Text, QuickReplies, Attachments}

    # ListMessage supports all types
    response = ListMessageResponse(data={}, header_type=HeaderType.NONE)
    assert set(response._components) == {Text, ListMessage}

    response = ListMessageResponse(data={}, header_type=HeaderType.TEXT)
    assert set(response._components) == {Text, ListMessage, Header}

    response = ListMessageResponse(data={}, header_type=HeaderType.ATTACHMENTS)
    assert set(response._components) == {Text, ListMessage, Attachments}


def test_footer_combinations():
    """Test footer combinations with different responses"""
    responses = [
        AttachmentResponse(data={}, footer=True),
        QuickReplyResponse(data={}, footer=True),
        ListMessageResponse(data={}, footer=True),
        CTAMessageResponse(data={}, footer=True),
        OrderDetailsResponse(data={}, footer=True),
    ]

    for response in responses:
        assert Footer in response._components


def test_required_components():
    """Test that required components are always present"""
    # Text is required for most responses, except for AttachmentResponse
    responses = [
        TextResponse(data={}),
        QuickReplyResponse(data={}),
        ListMessageResponse(data={}),
        CTAMessageResponse(data={}),
        OrderDetailsResponse(data={}),
        LocationResponse(data={}),
    ]

    for response in responses:
        assert Text in response._components


def test_response_data_handling():
    """Test that response data is handled correctly"""
    test_data = {"key": "value", "nested": {"test": True}}

    responses = [
        TextResponse(data=test_data),
        AttachmentResponse(data=test_data),
        QuickReplyResponse(data=test_data),
        ListMessageResponse(data=test_data),
        CTAMessageResponse(data=test_data),
        OrderDetailsResponse(data=test_data),
        LocationResponse(data=test_data),
    ]

    for response in responses:
        assert response._data == test_data
        # Ensure data is a copy
        assert response._data is not test_data
