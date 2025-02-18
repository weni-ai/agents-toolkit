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
    A response from a skill.
    """

    _data: dict = {}
    _components: list[Type[Component]] = []

    def __init__(self, data: dict, components: list[Type[Component]]):
        # Ensure data and components are immutable
        self._data = data.copy()
        self._components = components.copy()

    def __str__(self):
        # Get parsed components without additional JSON encoding
        parsed_components = [component.parse() for component in self._components]

        # Create the response structure
        response = {"data": self._data, "components": parsed_components}

        # Single JSON encoding
        return json.dumps(response)


class HeaderType(Enum):
    TEXT = "text"
    ATTACHMENTS = "attachments"
    NONE = "none"


class TextResponse(Response):
    """Type-safe Text response."""

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
    Type-safe QuickReply response with different header types.
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
    """Type-safe ListMessage response."""

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
    """Type-safe CTA response."""

    def __init__(self, data: Dict[str, Any], header: bool = False, footer: bool = False):
        components = [Text, CTAMessage]

        if header:
            components.append(Header)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class OrderDetailsResponse(Response):
    """Type-safe OrderDetails response."""

    def __init__(self, data: Dict[str, Any], attachments: bool = False, footer: bool = False):
        components = [Text, OrderDetails]

        if attachments:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        super().__init__(data=data, components=components)


class LocationResponse(Response):
    """Type-safe Location response."""

    def __init__(self, data: Dict[str, Any]):
        components = [Text, Location]
        super().__init__(data=data, components=components)
