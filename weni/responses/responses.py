import json
from enum import Enum
from typing import Dict, Any, Type
from weni.components import (
    Component,
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


class Response:
    """
    Base class for all skill response types.

    A Response encapsulates both the data returned by a skill and the components
    used to display that data. All response data and components are immutable
    after creation.

    Attributes:
        _data (dict): The immutable response data
        _components (list[Type[Component]]): List of component types used to display the data
    """

    _data: dict = {}
    _components: list[Type[Component]] = []

    def __init__(self, data: dict, components: list[Type[Component]]):
        # Ensure data and components are immutable
        self._data = data.copy()
        self._components = components.copy()

    def __str__(self):
        final_format = {"msg": {}}

        for component in self._components:
            final_format["msg"] = {**final_format["msg"], **component.get_format_example()}

        # Create the response structure
        response = {"data": self._data, "format": f"<example>{final_format}</example>"}

        # Single JSON encoding
        return json.dumps(response)


class HeaderType(Enum):
    """
    Defines the available header types for responses.
    """

    TEXT = "text"
    ATTACHMENTS = "attachments"
    NONE = "none"


class TextResponse(Response):
    """
    Type-safe Text response.

    Creates a response with a text message.

    Args:
        data (Dict[str, Any]): The response data
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data=data, components=[Text])


class AttachmentResponse(Response):
    """Type-safe Attachment response."""

    def __init__(self, data: Dict[str, Any], text: bool = False, footer: bool = False):
        components: list = [Attachments]

        if text:
            components.append(Text)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class QuickReplyResponse(Response):
    """
    Type-safe response for quick reply messages.

    Creates a response with quick reply buttons and optional header/footer.

    Args:
        data (Dict[str, Any]): The response data
        header_type (HeaderType): Type of header to display (default: HeaderType.NONE)
        footer (bool): Whether to include a footer (default: False)
    """

    def __init__(self, data: Dict[str, Any], header_type: HeaderType = HeaderType.NONE, footer: bool = False):
        components = [Text, QuickReplies]

        if header_type == HeaderType.TEXT:
            components.append(Header)
        elif header_type == HeaderType.ATTACHMENTS:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class ListMessageResponse(Response):
    """
    Type-safe ListMessage response.

    Creates a response with a list of items and optional header/footer.

    Args:
        data (Dict[str, Any]): The response data
        header_type (HeaderType): Type of header to display (default: HeaderType.NONE)
        footer (bool): Whether to include a footer (default: False)
    """

    def __init__(self, data: Dict[str, Any], header_type: HeaderType = HeaderType.NONE, footer: bool = False):
        components = [Text, ListMessage]

        if header_type == HeaderType.TEXT:
            components.append(Header)
        elif header_type == HeaderType.ATTACHMENTS:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class CTAMessageResponse(Response):
    """
    Type-safe CTA response.

    Creates a response with a call-to-action message and optional header/footer.

    Args:
        data (Dict[str, Any]): The response data
        header (bool): Whether to include a header (default: False)
        footer (bool): Whether to include a footer (default: False)
    """

    def __init__(self, data: Dict[str, Any], header: bool = False, footer: bool = False):
        components = [Text, CTAMessage]

        if header:
            components.append(Header)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class OrderDetailsResponse(Response):
    """
    Type-safe OrderDetails response.

    Creates a response with order details and optional attachments/footer.

    Args:
        data (Dict[str, Any]): The response data
    """

    def __init__(self, data: Dict[str, Any], attachments: bool = False, footer: bool = False):
        components = [Text, OrderDetails]

        if attachments:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class LocationResponse(Response):
    """
    Type-safe Location response.

    Creates a response with a location request and optional header/footer.

    Args:
        data (Dict[str, Any]): The response data
    """

    def __init__(self, data: Dict[str, Any]):
        components = [Text, Location]
        super().__init__(data=data, components=components)
