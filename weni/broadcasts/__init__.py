"""
Weni Broadcasts Module

Provides message types and broadcast functionality for sending
WhatsApp messages asynchronously during tool execution.

Example:
    ```python
    from weni.broadcasts import Broadcast, Text, Attachment

    class MyTool(Tool):
        def execute(self, context: Context):
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

from weni.broadcasts.broadcast import Broadcast
from weni.broadcasts.messages import (
    Message,
    Text,
    Attachment,
    QuickReply,
    ListMessage,
    CTAMessage,
    Location,
    OrderDetails,
    Catalog,
)

__all__ = [
    "Broadcast",
    "Message",
    "Text",
    "Attachment",
    "QuickReply",
    "ListMessage",
    "CTAMessage",
    "Location",
    "OrderDetails",
    "Catalog",
]
