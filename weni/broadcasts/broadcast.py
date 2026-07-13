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

    Shorthand via Tool:
        ``self.send_broadcast(message)`` is equivalent to ``self.broadcasts.send(message)``.
    """

    # Exposes self.send_broadcast on any Tool instance without adding a method to Tool.
    _tool_methods: dict[str, str] = {"send_broadcast": "send"}
    def __init__(self, tool: "Tool"):
        self._tool = tool

    def _get_sender(self) -> "BroadcastSender":
        from weni.broadcasts.sender import BroadcastSender
        return BroadcastSender(self._tool.context)

    def send(self, message: Message) -> None:
        """
        Send a broadcast message to the contact via the Flows API.

        Args:
            message: The Message object to send (Text, Attachment, etc.)
        """
        payload = message.format_message()
        self._tool._register_operation("messages_sent", payload)

        sender = self._get_sender()
        sender.send(payload)

    def send_many(self, messages: list[Message]) -> None:
        """
        Send multiple broadcast messages.

        Args:
            messages: List of Message objects to send.
        """
        if not messages:
            return

        payloads = [msg.format_message() for msg in messages]
        for payload in payloads:
            self._tool._register_operation("messages_sent", payload)

        sender = self._get_sender()
        sender.send_batch(payloads)
