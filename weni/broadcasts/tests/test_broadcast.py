"""
Tests for Broadcast class.
"""

from unittest.mock import MagicMock, patch

from weni.broadcasts.broadcast import Broadcast
from weni.broadcasts.messages import Text
from weni.context import Context


def create_context(
    project: dict | None = None,
    credentials: dict | None = None,
    globals: dict | None = None,
    contact: dict | None = None,
) -> Context:
    """Helper to create a Context for testing."""
    return Context(
        credentials=credentials or {},
        parameters={},
        globals=globals or {},
        contact=contact or {},
        project=project or {},
        constants={},
    )


class TestBroadcast:
    """Tests for Broadcast instance-based API."""

    def test_broadcast_requires_tool(self):
        """Test that Broadcast takes a tool instance."""
        mock_tool = MagicMock()
        mock_tool.context = create_context()
        mock_tool._pending_broadcasts = []

        broadcast = Broadcast(mock_tool)
        assert broadcast._tool is mock_tool

    @patch("weni.broadcasts.sender.BroadcastSender")
    def test_send_registers_and_sends(self, mock_sender_class):
        """Test that send registers the message on the tool and sends via HTTP."""
        mock_sender = MagicMock()
        mock_sender.send.return_value = {"id": 1}
        mock_sender_class.return_value = mock_sender

        mock_tool = MagicMock()
        mock_tool.context = create_context(project={"auth_token": "tk"})
        mock_tool._pending_broadcasts = []

        with patch.object(Broadcast, '_get_sender', return_value=mock_sender):
            broadcast = Broadcast(mock_tool)
            broadcast.send(Text(text="Hello!"))

        mock_tool.register_broadcast.assert_called_once_with({"text": "Hello!"})
        mock_sender.send.assert_called_once_with({"text": "Hello!"})

    @patch("weni.broadcasts.sender.BroadcastSender")
    def test_send_many_registers_all_and_sends_batch(self, mock_sender_class):
        """Test that send_many registers all messages and sends as batch."""
        mock_sender = MagicMock()
        mock_sender_class.return_value = mock_sender

        mock_tool = MagicMock()
        mock_tool.context = create_context(project={"auth_token": "tk"})
        mock_tool._pending_broadcasts = []

        with patch.object(Broadcast, '_get_sender', return_value=mock_sender):
            broadcast = Broadcast(mock_tool)
            broadcast.send_many([Text(text="Msg 1"), Text(text="Msg 2")])

        assert mock_tool.register_broadcast.call_count == 2
        mock_sender.send_batch.assert_called_once()
        payloads = mock_sender.send_batch.call_args[0][0]
        assert len(payloads) == 2
        assert payloads[0]["text"] == "Msg 1"
        assert payloads[1]["text"] == "Msg 2"

    def test_send_many_empty_does_nothing(self):
        """Test that send_many with empty list does nothing."""
        mock_tool = MagicMock()
        mock_tool.context = create_context()
        mock_tool._pending_broadcasts = []

        broadcast = Broadcast(mock_tool)
        broadcast.send_many([])

        mock_tool.register_broadcast.assert_not_called()


class TestBroadcastIsolation:
    """Tests that broadcasts are isolated per tool execution."""

    def test_register_broadcast_appends(self):
        """Test that register_broadcast appends to the tool's list."""
        from weni.tool import Tool

        mock_instance = object.__new__(Tool)
        mock_instance._pending_broadcasts = []

        mock_instance.register_broadcast({"text": "Hello"})
        mock_instance.register_broadcast({"text": "World"})

        assert len(mock_instance._pending_broadcasts) == 2
        assert mock_instance._pending_broadcasts[0]["text"] == "Hello"
        assert mock_instance._pending_broadcasts[1]["text"] == "World"

    def test_separate_tools_have_separate_broadcasts(self):
        """Test that two tool instances don't share broadcasts."""
        from weni.tool import Tool

        tool1 = object.__new__(Tool)
        tool1._pending_broadcasts = []

        tool2 = object.__new__(Tool)
        tool2._pending_broadcasts = []

        tool1.register_broadcast({"text": "From tool 1"})
        tool2.register_broadcast({"text": "From tool 2"})

        assert len(tool1._pending_broadcasts) == 1
        assert tool1._pending_broadcasts[0]["text"] == "From tool 1"
        assert len(tool2._pending_broadcasts) == 1
        assert tool2._pending_broadcasts[0]["text"] == "From tool 2"
