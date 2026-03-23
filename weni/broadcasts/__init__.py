"""
Weni Broadcasts Module

Provides message types and broadcast functionality for sending
WhatsApp messages during tool execution via the Flows API.

Example:
    ```python
    from weni.broadcasts import Broadcast, Text
    from weni.components import FinalResponse

    class MyTool(Tool):
        def execute(self, context: Context):
            Broadcast.send(Text(text="Processing your request..."))
            result = do_work()
            return FinalResponse()
    ```
"""

from weni.broadcasts.broadcast import Broadcast, BroadcastEvent
from weni.broadcasts.messages import (
    Catalog,
    Message,
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
    "QuickReply",
    "Catalog",
]
