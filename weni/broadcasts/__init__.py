"""
Weni Broadcasts Module

Provides message types and broadcast functionality for sending
WhatsApp messages asynchronously during tool execution.

Messages are sent to an SQS queue and processed by a Flows worker,
providing near-zero latency (~5-10ms) with 100% delivery guarantee.

Example:
    ```python
    from weni.broadcasts import Broadcast, Text, Attachment

    class MyTool(Tool):
        def execute(self, context: Context):
            # Configure the broadcast sender (required once)
            Broadcast.configure(context)

            # Send a text message
            Broadcast.send(Text(text="Processing your request..."))

            # Do some work...
            result = some_api_call()

            # Send an attachment
            Broadcast.send(Attachment(
                text="Here's the result",
                image="https://example.com/image.png"
            ))

            return FinalResponse()
    ```
"""

from weni.broadcasts.broadcast import Broadcast, BroadcastEvent
from weni.broadcasts.messages import (
    Attachment,
    Catalog,
    CTAMessage,
    ListItem,
    ListMessage,
    Location,
    Message,
    OrderDetails,
    OrderItem,
    QuickReply,
    Text,
)
from weni.broadcasts.sender import (
    BroadcastSender,
    BroadcastSenderConfigError,
    BroadcastSenderError,
)

__all__ = [
    # Main classes
    "Broadcast",
    "BroadcastEvent",
    "BroadcastSender",
    # Exceptions
    "BroadcastSenderError",
    "BroadcastSenderConfigError",
    # Message types
    "Message",
    "Text",
    "Attachment",
    "QuickReply",
    "ListItem",
    "ListMessage",
    "CTAMessage",
    "Location",
    "OrderItem",
    "OrderDetails",
    "Catalog",
]
