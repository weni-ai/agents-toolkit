"""
Tests for Broadcast class.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

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

    def test_pop_pending_returns_and_clears(self):
        """Test that pop_pending returns messages and clears them."""
        BroadcastEvent.register(Text(text="First"))
        BroadcastEvent.register(Text(text="Second"))

        # Pop should return all messages
        popped = BroadcastEvent.pop_pending()
        assert len(popped) == 2
        assert popped[0]["text"] == "First"
        assert popped[1]["text"] == "Second"

        # Should be empty now
        assert len(BroadcastEvent.get_pending()) == 0

    def test_pop_pending_returns_copy(self):
        """Test that pop_pending returns a copy that can be modified safely."""
        BroadcastEvent.register(Text(text="Hello"))
        popped = BroadcastEvent.pop_pending()

        # Modifying returned list shouldn't affect internal state
        popped.append({"text": "Should not appear"})

        # Register a new message
        BroadcastEvent.register(Text(text="New"))
        pending = BroadcastEvent.get_pending()

        assert len(pending) == 1
        assert pending[0]["text"] == "New"


class TestBroadcastEventScope:
    """Tests for BroadcastEvent.scope() context manager."""

    def setup_method(self):
        """Clear pending messages before each test."""
        BroadcastEvent.clear()

    def test_scope_provides_isolation(self):
        """Test that scope provides isolation for messages."""
        # Register a message outside any scope
        BroadcastEvent.register(Text(text="Outside"))

        with BroadcastEvent.scope():
            # Inside scope should start empty
            assert len(BroadcastEvent.get_pending()) == 0

            # Register messages inside scope
            BroadcastEvent.register(Text(text="Inside"))
            assert len(BroadcastEvent.get_pending()) == 1

        # After scope, should be back to original state
        pending = BroadcastEvent.get_pending()
        assert len(pending) == 1
        assert pending[0]["text"] == "Outside"

        # Cleanup
        BroadcastEvent.clear()

    def test_nested_scopes(self):
        """Test that nested scopes work correctly."""
        BroadcastEvent.register(Text(text="Level 0"))

        with BroadcastEvent.scope():
            BroadcastEvent.register(Text(text="Level 1"))
            assert len(BroadcastEvent.get_pending()) == 1

            with BroadcastEvent.scope():
                BroadcastEvent.register(Text(text="Level 2"))
                assert len(BroadcastEvent.get_pending()) == 1
                assert BroadcastEvent.get_pending()[0]["text"] == "Level 2"

            # Back to level 1
            assert len(BroadcastEvent.get_pending()) == 1
            assert BroadcastEvent.get_pending()[0]["text"] == "Level 1"

        # Back to level 0
        assert len(BroadcastEvent.get_pending()) == 1
        assert BroadcastEvent.get_pending()[0]["text"] == "Level 0"

        # Cleanup
        BroadcastEvent.clear()

    def test_scope_clears_on_exception(self):
        """Test that scope clears even when exception occurs."""
        BroadcastEvent.register(Text(text="Before"))

        try:
            with BroadcastEvent.scope():
                BroadcastEvent.register(Text(text="During"))
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should be back to original state
        pending = BroadcastEvent.get_pending()
        assert len(pending) == 1
        assert pending[0]["text"] == "Before"

        # Cleanup
        BroadcastEvent.clear()

    def test_scope_isolation_between_threads(self):
        """Test that scopes provide isolation between threads."""
        results: dict[str, list[dict]] = {}
        barrier = threading.Barrier(2)

        def worker(name: str) -> None:
            with BroadcastEvent.scope():
                BroadcastEvent.register(Text(text=f"Message from {name}"))
                # Synchronize to ensure both threads are running concurrently
                barrier.wait()
                # Each thread should only see its own message
                results[name] = BroadcastEvent.get_pending()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(worker, "thread1")
            future2 = executor.submit(worker, "thread2")
            future1.result()
            future2.result()

        # Each thread should have captured only its own message
        assert len(results["thread1"]) == 1
        assert results["thread1"][0]["text"] == "Message from thread1"
        assert len(results["thread2"]) == 1
        assert results["thread2"][0]["text"] == "Message from thread2"


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

    def test_send_within_scope(self):
        """Test that send works correctly within a scope."""
        with BroadcastEvent.scope():
            Broadcast.send(Text(text="Scoped message"))
            pending = BroadcastEvent.get_pending()
            assert len(pending) == 1
            assert pending[0]["text"] == "Scoped message"

        # After scope, should be empty (or back to original state)
        assert len(BroadcastEvent.get_pending()) == 0
