"""
Broadcast class for sending messages during tool execution.

This provides the foundation for sending WhatsApp messages
during tool execution via the Flows WhatsApp Broadcasts API.
"""

from typing import TYPE_CHECKING

from weni.broadcasts.messages import Message

if TYPE_CHECKING:
    from weni.broadcasts.sender import BroadcastSender
    from weni.tool import Tool

# Context variable for storing pending messages per execution context.
# This provides proper isolation between:
# - Concurrent tool executions
# - Sequential invocations in warm Lambda starts
# - Multiple requests in long-running processes
# Note: Default is None to avoid mutable default value sharing issues


class Broadcast:
    """
    Static class for sending broadcast messages during tool execution.

    Messages sent via Broadcast.send() are POSTed directly to the
    Flows WhatsApp Broadcasts API.

    Setup:
        The sender is automatically configured by Tool.__new__() using
        the execution context. No manual setup is needed.

    Example:
        ```python
        from weni.broadcasts import Broadcast, Text
        from weni.responses import FinalResponse

        class MyTool(Tool):
            def execute(self, context: Context):
                Broadcast(self).send(Text(text="Processing your request..."))
                result = do_work()
                return FinalResponse()
        ```
    """
    def __init__(self, tool: "Tool"):
        self._tool = tool

    def _get_sender(self) -> "BroadcastSender":
        from weni.broadcasts.sender import BroadcastSender
        return BroadcastSender(self._tool.context)

    def send(self, message: Message) -> None:
        """
        Send a broadcast message to the contact via the Flows API.

        If configure() hasn't been called, the message is only registered
        in BroadcastEvent for tracking (backward compatibility).

        Args:
            message: The Message object to send (Text, Attachment, etc.)
        """
        self._tool.register_broadcast(message.format_message())

        sender = self._get_sender()
        sender.send(message.format_message())

    def send_many(self, messages: list[Message]) -> None:
        """
        Send multiple broadcast messages.

        Args:
            messages: List of Message objects to send.
        """
        if not messages:
            return

        for message in messages:
            self._tool.register_broadcast(message.format_message())

        sender = self._get_sender()
        sender.send_batch([msg.format_message() for msg in messages])
