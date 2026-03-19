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
