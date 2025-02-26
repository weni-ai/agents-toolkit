import json
from enum import Enum
from typing import Dict, Any, Type, List
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
        _data (Dict[str, Any]): The immutable response data
        _components (List[Type[Component]]): List of component types used to display the data

    Args:
        data (Dict[str, Any]): The response data to be returned
        components (List[Type[Component]]): List of component types used for rendering
    """

    _data: Dict[str, Any] = {}
    _components: List[Type[Component]] = []

    def __init__(self, data: Dict[str, Any], components: List[Type[Component]]):
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

    Enum Values:
        TEXT: Use a text-based header
        ATTACHMENTS: Use an attachment-based header (images, files, etc.)
        NONE: Do not include a header
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

    Example:
        ```python
        response = TextResponse(data=api_response)
        ```
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data=data, components=[Text])


class AttachmentResponse(Response):
    """
    Type-safe Attachment response.

    Creates a response with attachments such as images, documents, or videos.

    Args:
        data (Dict[str, Any]): The response data
        text (bool): Whether to include a text component (default: False)
        footer (bool): Whether to include a footer component (default: False)

    Example:
        ```python
        response = AttachmentResponse(data=api_response, text=True, footer=True)
        ```
    """

    def __init__(self, data: Dict[str, Any], text: bool = False, footer: bool = False):
        components: List[Type[Component]] = [Attachments]

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

    Example:
        ```python
        response = QuickReplyResponse(data=api_response, header_type=HeaderType.TEXT, footer=True)
        ```
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

    Example:
        ```python
        response = ListMessageResponse(data=api_response, header_type=HeaderType.NONE, footer=True)
        ```
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
    Type-safe CTA (Call-to-Action) response.

    Creates a response with a call-to-action message and optional header/footer.

    Args:
        data (Dict[str, Any]): The response data
        header (bool): Whether to include a header component (default: False)
        footer (bool): Whether to include a footer component (default: False)

    Example:
        ```python
        response = CTAMessageResponse(data=api_response, header=True, footer=True)
        ```
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
        attachments (bool): Whether to include attachments (default: False)
        footer (bool): Whether to include a footer (default: False)

    Example:
        ```python
        response = OrderDetailsResponse(data=api_response, attachments=True, footer=True)
        ```
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

    Example:
        ```python
        response = LocationResponse(data=api_response)
        ```
    """

    def __init__(self, data: Dict[str, Any]):
        components = [Text, Location]
        super().__init__(data=data, components=components)
