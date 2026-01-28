"""
Tests for Broadcast class.
"""


from weni.broadcasts.broadcast import Broadcast, BroadcastEvent
from weni.broadcasts.messages import Text, Attachment


class TestBroadcastEvent:
    """Tests for BroadcastEvent registry."""

    def setup_method(self):
        """Clear pending messages before each test."""
        BroadcastEvent.clear()

    def test_register_message(self):
        """Test registering a message."""
        msg = Text(text="Hello")
        BroadcastEvent.register(msg)

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 1
        assert pending[0]["text"] == "Hello"

    def test_register_multiple_messages(self):
        """Test registering multiple messages."""
        BroadcastEvent.register(Text(text="First"))
        BroadcastEvent.register(Text(text="Second"))

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 2

    def test_clear_messages(self):
        """Test clearing pending messages."""
        BroadcastEvent.register(Text(text="Hello"))
        BroadcastEvent.clear()

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 0

    def test_get_pending_returns_copy(self):
        """Test that get_pending returns a copy."""
        BroadcastEvent.register(Text(text="Hello"))
        pending = BroadcastEvent.get_pending()
        pending.clear()

        # Original should still have the message
        assert len(BroadcastEvent.get_pending()) == 1


class TestBroadcast:
    """Tests for Broadcast class."""

    def setup_method(self):
        """Clear pending messages before each test."""
        BroadcastEvent.clear()

    def test_send_text(self):
        """Test sending a text message."""
        Broadcast.send(Text(text="Hello!"))

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 1
        assert pending[0]["type"] == "text"
        assert pending[0]["text"] == "Hello!"

    def test_send_attachment(self):
        """Test sending an attachment."""
        Broadcast.send(Attachment(text="Image", image="https://example.com/img.png"))

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 1
        assert pending[0]["type"] == "attachment"

    def test_send_multiple(self):
        """Test sending multiple messages."""
        Broadcast.send(Text(text="Processing..."))
        Broadcast.send(Attachment(image="https://example.com/result.png"))

        pending = BroadcastEvent.get_pending()
        assert len(pending) == 2
        assert pending[0]["type"] == "text"
        assert pending[1]["type"] == "attachment"
