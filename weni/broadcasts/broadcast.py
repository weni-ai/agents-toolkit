"""
Broadcast class for sending messages during tool execution.

This provides the foundation for sending WhatsApp messages
during tool execution via the Flows WhatsApp Broadcasts API.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Generator

from weni.broadcasts.messages import Message

if TYPE_CHECKING:
    from weni.broadcasts.sender import BroadcastSender
    from weni.context import Context

# Context variable for storing pending messages per execution context.
# This provides proper isolation between:
# - Concurrent tool executions
# - Sequential invocations in warm Lambda starts
# - Multiple requests in long-running processes
# Note: Default is None to avoid mutable default value sharing issues
_pending_messages_var: ContextVar[list[dict] | None] = ContextVar("pending_messages", default=None)

# Context variable for storing the BroadcastSender instance
_sender_var: ContextVar["BroadcastSender | None"] = ContextVar("broadcast_sender", default=None)


class BroadcastEvent:
    """
    Event registry for broadcast messages.

    Stores messages that will be sent asynchronously after tool execution.
    This allows the tool to continue processing while messages are queued.

    Messages are stored in a context variable to ensure isolation between
    different tool executions, even in warm Lambda starts or long-running
    processes.

    For proper isolation, use the context manager:
        with BroadcastEvent.scope():
            Broadcast.send(Text(text="Hello"))
            # Messages are automatically isolated to this scope
    """

    @classmethod
    def _get_messages(cls) -> list[dict]:
        """Get the current context's message list, creating if needed."""
        messages = _pending_messages_var.get()
        if messages is None:
            messages = []
            _pending_messages_var.set(messages)
        return messages

    @classmethod
    def register(cls, message: Message) -> None:
        """
        Register a message to be sent.

        Args:
            message: The Message object to register.
        """
        payload = message.format_message()
        messages = cls._get_messages()
        messages.append(payload)

    @classmethod
    def get_pending(cls) -> list[dict]:
        """
        Get all pending messages.

        Returns:
            List of message payloads (copy of internal list).
        """
        return cls._get_messages().copy()

    @classmethod
    def pop_pending(cls) -> list[dict]:
        """
        Get and clear all pending messages atomically.

        This is useful for the actual send implementation to ensure
        messages are retrieved and cleared in one operation.

        Returns:
            List of message payloads that were pending.
        """
        messages = cls._get_messages()
        result = messages.copy()
        messages.clear()
        return result

    @classmethod
    def clear(cls) -> None:
        """Clear all pending messages in the current context."""
        cls._get_messages().clear()

    @classmethod
    @contextmanager
    def scope(cls) -> Generator[None, None, None]:
        """
        Context manager for scoped broadcast message handling.

        Creates an isolated scope for broadcast messages. Messages registered
        within this scope are automatically cleared when the scope exits.

        This is the recommended way to handle broadcasts in tool execution
        to ensure proper isolation between invocations.

        Example:
            with BroadcastEvent.scope():
                Broadcast.send(Text(text="Processing..."))
                # do work
                messages = BroadcastEvent.pop_pending()
                # send messages to API

        Yields:
            None
        """
        # Create a new list for this scope
        token = _pending_messages_var.set([])
        try:
            yield
        finally:
            # Reset to previous value (or default)
            _pending_messages_var.reset(token)


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
        from weni.components import FinalResponse

        class MyTool(Tool):
            def execute(self, context: Context):
                Broadcast.send(Text(text="Processing your request..."))
                result = do_work()
                return FinalResponse()
        ```
    """

    @staticmethod
    def configure(context: "Context") -> None:
        """
        Configure the broadcast sender with the execution context.

        Called automatically by Tool.__new__(). No manual call needed.

        Args:
            context: The execution context containing configuration.

        Raises:
            BroadcastSenderConfigError: If required configuration is missing.
        """
        from weni.broadcasts.sender import BroadcastSender

        sender = BroadcastSender(context)
        _sender_var.set(sender)

    @staticmethod
    def _get_sender() -> "BroadcastSender | None":
        """Get the configured sender from context variable."""
        return _sender_var.get()

    @staticmethod
    def send(message: Message) -> None:
        """
        Send a broadcast message to the contact via the Flows API.

        If configure() hasn't been called, the message is only registered
        in BroadcastEvent for tracking (backward compatibility).

        Args:
            message: The Message object to send (Text, Attachment, etc.)
        """
        BroadcastEvent.register(message)

        sender = Broadcast._get_sender()
        if sender is not None:
            payload = message.format_message()
            sender.send(payload)

    @staticmethod
    def send_many(messages: list[Message]) -> None:
        """
        Send multiple broadcast messages.

        Args:
            messages: List of Message objects to send.
        """
        if not messages:
            return

        for message in messages:
            BroadcastEvent.register(message)

        sender = Broadcast._get_sender()
        if sender is not None:
            payloads = [msg.format_message() for msg in messages]
            sender.send_batch(payloads)

    @staticmethod
    def flush() -> list[dict]:
        """
        Get and clear all pending messages.

        This is useful for debugging or for scenarios where you need
        to process messages differently.

        Returns:
            List of message payloads that were pending.
        """
        return BroadcastEvent.pop_pending()

    @staticmethod
    def get_broadcasts() -> list[dict]:
        """
        Get all broadcasts that were sent during this execution.

        Returns:
            List of message payloads that were sent.
        """
        return BroadcastEvent.get_pending()
