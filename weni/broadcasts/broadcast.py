"""
Broadcast class for sending messages during tool execution.

This provides the foundation for sending WhatsApp messages asynchronously
during tool execution, without blocking the main response.
"""

from typing import TYPE_CHECKING

from weni.broadcasts.messages import Message

if TYPE_CHECKING:
    pass


class BroadcastEvent:
    """
    Event registry for broadcast messages.
    
    Stores messages that will be sent asynchronously after tool execution.
    This allows the tool to continue processing while messages are queued.
    """
    
    _pending_messages: list[dict] = []
    
    @classmethod
    def register(cls, message: Message) -> None:
        """
        Register a message to be sent.
        
        Args:
            message: The Message object to register.
        """
        payload = message.format_message()
        cls._pending_messages.append(payload)
    
    @classmethod
    def get_pending(cls) -> list[dict]:
        """
        Get all pending messages.
        
        Returns:
            List of message payloads.
        """
        return cls._pending_messages.copy()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all pending messages."""
        cls._pending_messages = []


class Broadcast:
    """
    Static class for sending broadcast messages during tool execution.
    
    Messages sent via Broadcast.send() are queued and sent asynchronously
    to the contact, without adding latency to the tool's response.
    
    Example:
        ```python
        from weni.broadcasts import Broadcast, Text, Attachment
        
        class MyTool(Tool):
            def execute(self, context: Context):
                # Send immediate feedback to user
                Broadcast.send(Text(text="Processing your request..."))
                
                # Do some work
                result = expensive_api_call()
                
                # Send result as attachment
                Broadcast.send(Attachment(
                    text="Here's what I found",
                    image=result["image_url"]
                ))
                
                return FinalResponse()
        ```
    
    Note:
        The actual HTTP call to the Flows API will be implemented in a future task.
        Currently, messages are registered in BroadcastEvent for later processing.
    """
    
    @staticmethod
    def send(message: Message) -> None:
        """
        Queue a message to be sent to the contact.
        
        The message is registered in BroadcastEvent and will be sent
        asynchronously after tool execution completes.
        
        Args:
            message: The Message object to send (Text, Attachment, etc.)
        
        Example:
            ```python
            Broadcast.send(Text(text="Hello!"))
            Broadcast.send(Attachment(text="Image", image="https://..."))
            ```
        """
        BroadcastEvent.register(message)
        
        # TODO: In the next task, implement the actual HTTP call:
        # msg_payload = message.format_message()
        # http.post("https://flows.weni.ai/api/v2/internals/whatsapp_broadcasts", msg_payload)
