"""
Tests for BroadcastSender class.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from weni.broadcasts.sender import (
    BroadcastSender,
    BroadcastSenderConfigError,
    BroadcastSenderError,
)
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
    )


class TestBroadcastSenderInit:
    """Tests for BroadcastSender initialization."""

    def test_init_with_all_config_in_project(self):
        """Test initialization with all config in project."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue",
                "flows_url": "https://flows.weni.ai",
                "flows_jwt": "jwt-token-123",
                "project_uuid": "proj-uuid-123",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.queue_url == "https://sqs.us-east-1.amazonaws.com/123/queue"
        assert sender.flows_url == "https://flows.weni.ai"
        assert sender.jwt_token == "jwt-token-123"
        assert sender.project_uuid == "proj-uuid-123"

    def test_init_with_config_in_credentials(self):
        """Test initialization with config in credentials."""
        context = create_context(
            credentials={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue",
                "flows_url": "https://flows.weni.ai",
                "flows_jwt": "jwt-token-123",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.queue_url == "https://sqs.us-east-1.amazonaws.com/123/queue"
        assert sender.flows_url == "https://flows.weni.ai"
        assert sender.jwt_token == "jwt-token-123"

    def test_init_with_config_in_globals(self):
        """Test initialization with config in globals."""
        context = create_context(
            globals={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue",
                "flows_url": "https://flows.weni.ai",
            },
            credentials={"flows_jwt": "jwt-token-123"},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.queue_url == "https://sqs.us-east-1.amazonaws.com/123/queue"
        assert sender.flows_url == "https://flows.weni.ai"

    @patch.dict(os.environ, {"BROADCAST_SQS_QUEUE_URL": "https://sqs.env/queue", "FLOWS_BASE_URL": "https://flows.env"})
    def test_init_with_config_in_env(self):
        """Test initialization with config in environment variables."""
        context = create_context(credentials={"flows_jwt": "jwt-token"})

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.queue_url == "https://sqs.env/queue"
        assert sender.flows_url == "https://flows.env"

    def test_init_project_overrides_credentials(self):
        """Test that project config takes priority over credentials."""
        context = create_context(
            project={"sqs_queue_url": "https://sqs.project/queue", "flows_url": "https://flows.project"},
            credentials={"sqs_queue_url": "https://sqs.creds/queue", "flows_url": "https://flows.creds"},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.queue_url == "https://sqs.project/queue"
        assert sender.flows_url == "https://flows.project"

    def test_init_missing_queue_url_raises(self):
        """Test that missing queue URL raises error."""
        context = create_context(
            project={"flows_url": "https://flows.weni.ai", "flows_jwt": "jwt-token"}
        )

        with pytest.raises(BroadcastSenderConfigError) as exc_info:
            BroadcastSender(context)

        assert "sqs_queue_url" in str(exc_info.value)

    def test_init_missing_flows_url_raises(self):
        """Test that missing flows URL raises error."""
        context = create_context(
            project={"sqs_queue_url": "https://sqs/queue", "flows_jwt": "jwt-token"}
        )

        with pytest.raises(BroadcastSenderConfigError) as exc_info:
            BroadcastSender(context)

        assert "flows_url" in str(exc_info.value)

    def test_init_jwt_token_optional(self):
        """Test that JWT token is optional (doesn't raise if missing)."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.jwt_token is None

    def test_jwt_token_from_jwt_key(self):
        """Test that JWT can be read from 'jwt' key as fallback."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
                "jwt": "fallback-jwt-token",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender.jwt_token == "fallback-jwt-token"


class TestBroadcastSenderContactUrn:
    """Tests for contact URN extraction."""

    def test_get_contact_urn_from_urns_list(self):
        """Test extracting URN from urns list."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            },
            contact={"urns": ["whatsapp:5511999999999", "tel:+5511999999999"]},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_contact_urn() == "whatsapp:5511999999999"

    def test_get_contact_urn_from_urn_field(self):
        """Test extracting URN from urn field."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            },
            contact={"urn": "whatsapp:5511999999999"},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_contact_urn() == "whatsapp:5511999999999"

    def test_get_contact_urn_empty_urns(self):
        """Test with empty urns list."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            },
            contact={"urns": []},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_contact_urn() is None

    def test_get_contact_urn_no_contact(self):
        """Test with no contact info."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_contact_urn() is None


class TestBroadcastSenderBuildPayload:
    """Tests for payload building."""

    def test_build_payload_basic(self):
        """Test building basic payload."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
                "flows_jwt": "jwt-token-123",
                "project_uuid": "proj-uuid",
            },
            contact={"urns": ["whatsapp:5511999999999"]},
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        message_payload = {"text": "Hello World"}
        payload = sender.build_payload(message_payload)

        assert payload["msg"] == {"text": "Hello World"}
        assert payload["flows_url"] == "https://flows.weni.ai"
        assert payload["urns"] == ["whatsapp:5511999999999"]
        assert payload["jwt_token"] == "jwt-token-123"
        assert payload["project_uuid"] == "proj-uuid"

    def test_build_payload_without_urn(self):
        """Test payload without contact URN."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        message_payload = {"text": "Hello"}
        payload = sender.build_payload(message_payload)

        assert "urns" not in payload

    def test_build_payload_without_jwt(self):
        """Test payload without JWT token."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        message_payload = {"text": "Hello"}
        payload = sender.build_payload(message_payload)

        assert "jwt_token" not in payload


class TestBroadcastSenderSend:
    """Tests for sending messages to SQS."""

    def test_send_success(self):
        """Test successful send to SQS."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue",
                "flows_url": "https://flows.weni.ai",
                "flows_jwt": "jwt-token",
            },
            contact={"urns": ["whatsapp:5511999999999"]},
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        result = sender.send({"text": "Hello!"})

        assert result["MessageId"] == "msg-123"
        mock_sqs.send_message.assert_called_once()

        # Verify the call arguments
        call_args = mock_sqs.send_message.call_args
        assert call_args.kwargs["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/123/queue"

        body = json.loads(call_args.kwargs["MessageBody"])
        assert body["msg"]["text"] == "Hello!"
        assert body["flows_url"] == "https://flows.weni.ai"
        assert body["urns"] == ["whatsapp:5511999999999"]
        assert body["jwt_token"] == "jwt-token"

    def test_send_sqs_error(self):
        """Test handling SQS errors."""
        from botocore.exceptions import ClientError

        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "SendMessage",
        )

        sender = BroadcastSender(context, sqs_client=mock_sqs)

        with pytest.raises(BroadcastSenderError) as exc_info:
            sender.send({"text": "Hello"})

        assert "Failed to send message to SQS" in str(exc_info.value)


class TestBroadcastSenderSendBatch:
    """Tests for batch sending messages to SQS."""

    def test_send_batch_success(self):
        """Test successful batch send."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            },
            contact={"urns": ["whatsapp:5511999999999"]},
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": "0", "MessageId": "msg-1"}, {"Id": "1", "MessageId": "msg-2"}],
            "Failed": [],
        }

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        result = sender.send_batch([{"text": "Message 1"}, {"text": "Message 2"}])

        assert len(result["Successful"]) == 2
        assert len(result["Failed"]) == 0

        mock_sqs.send_message_batch.assert_called_once()
        call_args = mock_sqs.send_message_batch.call_args
        assert len(call_args.kwargs["Entries"]) == 2

    def test_send_batch_empty_list(self):
        """Test batch send with empty list."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        result = sender.send_batch([])

        assert result == {"Successful": [], "Failed": []}
        mock_sqs.send_message_batch.assert_not_called()

    def test_send_batch_sqs_error(self):
        """Test handling SQS errors in batch."""
        from botocore.exceptions import ClientError

        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message_batch.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service Unavailable"}},
            "SendMessageBatch",
        )

        sender = BroadcastSender(context, sqs_client=mock_sqs)

        with pytest.raises(BroadcastSenderError) as exc_info:
            sender.send_batch([{"text": "Hello"}])

        assert "Failed to send batch to SQS" in str(exc_info.value)


class TestBroadcastSenderLazyClient:
    """Tests for lazy SQS client initialization."""

    @patch("weni.broadcasts.sender.boto3")
    def test_lazy_sqs_client_creation(self, mock_boto3):
        """Test that SQS client is created lazily."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        sender = BroadcastSender(context)

        # Client should not be created yet
        mock_boto3.client.assert_not_called()

        # Access the client
        client = sender.sqs_client

        # Now it should be created
        mock_boto3.client.assert_called_once_with("sqs")
        assert client == mock_client

        # Second access should not create a new client
        client2 = sender.sqs_client
        assert mock_boto3.client.call_count == 1
        assert client2 == mock_client


class TestBroadcastSenderFifo:
    """Tests for FIFO queue support."""

    def test_is_fifo_detected_by_url_suffix(self):
        """Test that FIFO queues are detected by .fifo suffix."""
        fifo_context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/my-queue.fifo",
                "flows_url": "https://flows.weni.ai",
            }
        )

        standard_context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/my-queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        fifo_sender = BroadcastSender(fifo_context, sqs_client=mock_sqs)
        standard_sender = BroadcastSender(standard_context, sqs_client=mock_sqs)

        assert fifo_sender.is_fifo is True
        assert standard_sender.is_fifo is False

    def test_message_group_id_uses_project_uuid(self):
        """Test that MessageGroupId uses project_uuid when available."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue.fifo",
                "flows_url": "https://flows.weni.ai",
                "project_uuid": "proj-123-abc",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_message_group_id() == "proj-123-abc"

    def test_message_group_id_default_fallback(self):
        """Test that MessageGroupId falls back to default when no project_uuid."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue.fifo",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        assert sender._get_message_group_id() == "default-broadcast-group"

    def test_deduplication_id_is_unique(self):
        """Test that each deduplication ID is unique."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue.fifo",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        sender = BroadcastSender(context, sqs_client=mock_sqs)

        ids = [sender._generate_deduplication_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_send_fifo_includes_fifo_params(self):
        """Test that send includes FIFO parameters for FIFO queues."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue.fifo",
                "flows_url": "https://flows.weni.ai",
                "project_uuid": "proj-uuid-123",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        sender.send({"text": "Hello FIFO!"})

        call_args = mock_sqs.send_message.call_args
        assert call_args.kwargs["MessageGroupId"] == "proj-uuid-123"
        assert "MessageDeduplicationId" in call_args.kwargs
        # Verify deduplication ID is a valid UUID format
        assert len(call_args.kwargs["MessageDeduplicationId"]) == 36

    def test_send_standard_excludes_fifo_params(self):
        """Test that send excludes FIFO parameters for standard queues."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        sender.send({"text": "Hello Standard!"})

        call_args = mock_sqs.send_message.call_args
        assert "MessageGroupId" not in call_args.kwargs
        assert "MessageDeduplicationId" not in call_args.kwargs

    def test_send_batch_fifo_includes_fifo_params(self):
        """Test that send_batch includes FIFO parameters for each entry."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue.fifo",
                "flows_url": "https://flows.weni.ai",
                "project_uuid": "proj-uuid",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": "0"}, {"Id": "1"}],
            "Failed": [],
        }

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        sender.send_batch([{"text": "Msg 1"}, {"text": "Msg 2"}])

        call_args = mock_sqs.send_message_batch.call_args
        entries = call_args.kwargs["Entries"]

        assert len(entries) == 2
        for entry in entries:
            assert entry["MessageGroupId"] == "proj-uuid"
            assert "MessageDeduplicationId" in entry

        # Deduplication IDs should be unique
        dedup_ids = [e["MessageDeduplicationId"] for e in entries]
        assert len(set(dedup_ids)) == 2

    def test_send_batch_standard_excludes_fifo_params(self):
        """Test that send_batch excludes FIFO parameters for standard queues."""
        context = create_context(
            project={
                "sqs_queue_url": "https://sqs/queue",
                "flows_url": "https://flows.weni.ai",
            }
        )

        mock_sqs = MagicMock()
        mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": "0"}],
            "Failed": [],
        }

        sender = BroadcastSender(context, sqs_client=mock_sqs)
        sender.send_batch([{"text": "Msg 1"}])

        call_args = mock_sqs.send_message_batch.call_args
        entries = call_args.kwargs["Entries"]

        for entry in entries:
            assert "MessageGroupId" not in entry
            assert "MessageDeduplicationId" not in entry
