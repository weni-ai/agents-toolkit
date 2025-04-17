from enum import Enum
from copy import deepcopy
from typing import Any, Type
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
from weni.validators.validators import validate_components


# All Reponse() calls should return a ResponseObject
# We've added type: ignore in all return statements since __new__ return type is ignored by mypy for now
# see https://github.com/python/mypy/issues/15182
ResponseObject = tuple[Any, dict[str, Any]]


class Response:
    """
    Base class for all tool response types.

    A Response encapsulates both the data returned by a tool and the components
    used to display that data. All response data and components are immutable
    after creation.

    Attributes:
        _data (Any): The immutable response data
        _components (list[Type[Component]]): List of component types used to display the data

    Args:
        data (Any): The response data to be returned
        components (list[Type[Component]]): List of component types used for rendering
    """

    _data: Any = {}
    _components: list[Type[Component]] = []

    def __new__(cls, data: Any, components: list[Type[Component]]) -> ResponseObject:  # type: ignore
        instance = super().__new__(cls)
        instance._data = deepcopy(data)
        instance._components = deepcopy(components)

        validate_components(instance._components)

        final_format: dict[str, Any] = {"msg": {}}

        for component in instance._components:
            final_format["msg"] = {**final_format["msg"], **component.get_format_example()}

        return instance._data, final_format


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
        data (Any): The response data

    Example:
        ```python
        result, format = TextResponse(data=api_response)
        ```
    """

    def __new__(cls, data: Any) -> ResponseObject:  # type: ignore
        return super().__new__(cls, data=data, components=[Text])


class AttachmentResponse(Response):
    """
    Type-safe Attachment response.

    Creates a response with attachments such as images, documents, or videos.

    Args:
        data (Any): The response data
        text (bool): Whether to include a text component (default: False)
        footer (bool): Whether to include a footer component (default: False)

    Example:
        ```python
        result, format = AttachmentResponse(data=api_response, text=True, footer=True)
        ```
    """

    def __new__(cls, data: Any, text: bool = False, footer: bool = False) -> ResponseObject:  # type: ignore
        components: list[Type[Component]] = [Attachments]

        if text:
            components.append(Text)

        if footer:
            components.append(Footer)

        return super().__new__(cls, data=data, components=components)


class QuickReplyResponse(Response):
    """
    Type-safe response for quick reply messages.

    Creates a response with quick reply buttons and optional header/footer.

    Args:
        data (Any): The response data
        header_type (HeaderType): Type of header to display (default: HeaderType.NONE)
        footer (bool): Whether to include a footer (default: False)

    Example:
        ```python
        result, format = QuickReplyResponse(data=api_response, header_type=HeaderType.TEXT, footer=True)
        ```
    """

    def __new__(cls, data: Any, header_type: HeaderType = HeaderType.NONE, footer: bool = False) -> ResponseObject:  # type: ignore
        components = [Text, QuickReplies]

        if header_type == HeaderType.TEXT:
            components.append(Header)
        elif header_type == HeaderType.ATTACHMENTS:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        return super().__new__(cls, data=data, components=components)


class ListMessageResponse(Response):
    """
    Type-safe ListMessage response.

    Creates a response with a list of items and optional header/footer.

    Args:
        data (Any): The response data
        header_type (HeaderType): Type of header to display (default: HeaderType.NONE)
        footer (bool): Whether to include a footer (default: False)

    Example:
        ```python
        result, format = ListMessageResponse(data=api_response, header_type=HeaderType.NONE, footer=True)
        ```
    """

    def __new__(cls, data: Any, header_type: HeaderType = HeaderType.NONE, footer: bool = False) -> ResponseObject:  # type: ignore
        components = [Text, ListMessage]

        if header_type == HeaderType.TEXT:
            components.append(Header)
        elif header_type == HeaderType.ATTACHMENTS:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        return super().__new__(cls, data=data, components=components)


class CTAMessageResponse(Response):
    """
    Type-safe CTA (Call-to-Action) response.

    Creates a response with a call-to-action message and optional header/footer.

    Args:
        data (Any): The response data
        header (bool): Whether to include a header component (default: False)
        footer (bool): Whether to include a footer component (default: False)

    Example:
        ```python
        result, format = CTAMessageResponse(data=api_response, header=True, footer=True)
        ```
    """

    def __new__(cls, data: Any, header: bool = False, footer: bool = False) -> ResponseObject:  # type: ignore
        components = [Text, CTAMessage]

        if header:
            components.append(Header)

        if footer:
            components.append(Footer)

        return super().__new__(cls, data=data, components=components)


class OrderDetailsResponse(Response):
    """
    Type-safe OrderDetails response.

    Creates a response with order details and optional attachments/footer.

    Args:
        data (Any): The response data
        attachments (bool): Whether to include attachments (default: False)
        footer (bool): Whether to include a footer (default: False)

    Example:
        ```python
        result, format = OrderDetailsResponse(data=api_response, attachments=True, footer=True)
        ```
    """

    def __new__(cls, data: Any, attachments: bool = False, footer: bool = False) -> ResponseObject:  # type: ignore
        components = [Text, OrderDetails]

        if attachments:
            components.append(Attachments)

        if footer:
            components.append(Footer)

        return super().__new__(cls, data=data, components=components)


class LocationResponse(Response):
    """
    Type-safe Location response.

    Creates a response with a location request and optional header/footer.

    Args:
        data (Any): The response data

    Example:
        ```python
        result, format = LocationResponse(data=api_response)
        ```
    """

    def __new__(cls, data: Any) -> ResponseObject:  # type: ignore
        return super().__new__(cls, data=data, components=[Text, Location])
