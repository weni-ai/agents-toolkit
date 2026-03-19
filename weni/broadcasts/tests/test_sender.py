"""
Tests for BroadcastSender class (HTTP-based).
"""

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
    parameters: dict | None = None,
) -> Context:
    """Helper to create a Context for testing."""
    return Context(
        credentials=credentials or {},
        parameters=parameters or {},
        globals=globals or {},
        contact=contact or {},
        project=project or {},
        constants={},
    )


def _default_project(**overrides) -> dict:
    base = {"flows_url": "https://flows.weni.ai", "auth_token": "test-token"}
    base.update(overrides)
    return base


class TestBroadcastSenderInit:
    def test_init_with_project_config(self):
        context = create_context(project=_default_project(uuid="proj-123", channel_uuid="ch-456"))
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.weni.ai"
        assert sender.auth_token == "test-token"
        assert sender.project_uuid == "proj-123"
        assert sender.channel_uuid == "ch-456"

    def test_init_with_credentials(self):
        context = create_context(credentials={"flows_url": "https://flows.creds.ai"}, project={"auth_token": "tk"})
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.creds.ai"

    def test_init_with_globals(self):
        context = create_context(globals={"flows_url": "https://flows.globals.ai"}, project={"auth_token": "tk"})
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.globals.ai"

    @patch.dict(os.environ, {"FLOWS_BASE_URL": "https://flows.env.ai"})
    def test_init_with_env_var(self):
        context = create_context(project={"auth_token": "tk"})
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.env.ai"

    def test_init_project_overrides_credentials(self):
        context = create_context(
            project={"flows_url": "https://flows.project", "auth_token": "tk"},
            credentials={"flows_url": "https://flows.creds"},
        )
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.project"

    def test_init_falls_back_to_default_flows_url(self):
        context = create_context(project={"auth_token": "tk"})
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.stg.cloud.weni.ai"

    def test_init_auth_token_optional(self):
        context = create_context(project={"flows_url": "https://flows.weni.ai"})
        sender = BroadcastSender(context)

        assert sender.auth_token is None

    def test_flows_url_trailing_slash_stripped(self):
        context = create_context(project=_default_project(flows_url="https://flows.weni.ai/"))
        sender = BroadcastSender(context)

        assert sender.flows_url == "https://flows.weni.ai"


class TestBroadcastSenderContactUrn:
    def test_from_urns_list(self):
        context = create_context(
            project=_default_project(),
            contact={"urns": ["whatsapp:5511999999999", "tel:+5511999999999"]},
        )
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() == "whatsapp:5511999999999"

    def test_from_urn_field(self):
        context = create_context(project=_default_project(), contact={"urn": "whatsapp:5511999999999"})
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() == "whatsapp:5511999999999"

    def test_from_parameters_fallback(self):
        context = create_context(project=_default_project(), parameters={"contact_urn": "whatsapp:5584988242399"})
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() == "whatsapp:5584988242399"

    def test_contact_takes_priority_over_parameters(self):
        context = create_context(
            project=_default_project(),
            contact={"urns": ["whatsapp:5511999999999"]},
            parameters={"contact_urn": "whatsapp:5584988242399"},
        )
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() == "whatsapp:5511999999999"

    def test_empty_urns_list(self):
        context = create_context(project=_default_project(), contact={"urns": []})
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() is None

    def test_no_contact_no_parameters(self):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)
        assert sender._get_contact_urn() is None


class TestBroadcastSenderBuildRequestBody:
    def test_basic_body(self):
        context = create_context(
            project=_default_project(channel_uuid="ch-123"),
            contact={"urns": ["whatsapp:5511999999999"]},
        )
        sender = BroadcastSender(context)
        body = sender._build_request_body({"text": "Hello"})

        assert body == {
            "msg": {"text": "Hello"},
            "urns": ["whatsapp:5511999999999"],
            "channel": "ch-123",
        }

    def test_body_without_urn(self):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)
        body = sender._build_request_body({"text": "Hello"})

        assert "urns" not in body

    def test_body_without_channel(self):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)
        body = sender._build_request_body({"text": "Hello"})

        assert "channel" not in body


class TestBroadcastSenderURL:
    def test_build_url(self):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)

        assert sender._build_url() == "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json"

    def test_build_url_no_double_slash(self):
        context = create_context(project=_default_project(flows_url="https://flows.weni.ai/"))
        sender = BroadcastSender(context)

        assert sender._build_url() == "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json"


class TestBroadcastSenderHeaders:
    def test_headers_with_token(self):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)
        headers = sender._build_headers()

        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
        }

    def test_headers_without_token(self):
        context = create_context(project={"flows_url": "https://flows.weni.ai"})
        sender = BroadcastSender(context)
        headers = sender._build_headers()

        assert headers == {"Content-Type": "application/json"}
        assert "Authorization" not in headers


class TestBroadcastSenderSend:
    @patch("weni.broadcasts.sender.requests.post")
    def test_send_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 5104}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        context = create_context(
            project=_default_project(channel_uuid="ch-123"),
            contact={"urns": ["whatsapp:5511999999999"]},
        )
        sender = BroadcastSender(context)
        result = sender.send({"text": "Hello!"})

        assert result == {"id": 5104}
        mock_post.assert_called_once_with(
            "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
            headers={"Content-Type": "application/json", "Authorization": "Bearer test-token"},
            json={"msg": {"text": "Hello!"}, "urns": ["whatsapp:5511999999999"], "channel": "ch-123"},
        )

    @patch("weni.broadcasts.sender.requests.post")
    def test_send_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"detail": "Invalid URN"}'
        mock_response.raise_for_status.side_effect = __import__("requests").exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        context = create_context(project=_default_project())
        sender = BroadcastSender(context)

        with pytest.raises(BroadcastSenderError) as exc_info:
            sender.send({"text": "Hello"})

        assert "400" in str(exc_info.value)

    @patch("weni.broadcasts.sender.requests.post")
    def test_send_connection_error(self, mock_post):
        mock_post.side_effect = __import__("requests").exceptions.ConnectionError("Connection refused")

        context = create_context(project=_default_project())
        sender = BroadcastSender(context)

        with pytest.raises(BroadcastSenderError) as exc_info:
            sender.send({"text": "Hello"})

        assert "Failed to send broadcast" in str(exc_info.value)


class TestBroadcastSenderSendBatch:
    @patch("weni.broadcasts.sender.requests.post")
    def test_send_batch(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        context = create_context(project=_default_project(), contact={"urns": ["whatsapp:5511999999999"]})
        sender = BroadcastSender(context)
        results = sender.send_batch([{"text": "Msg 1"}, {"text": "Msg 2"}])

        assert len(results) == 2
        assert mock_post.call_count == 2

    @patch("weni.broadcasts.sender.requests.post")
    def test_send_batch_empty(self, mock_post):
        context = create_context(project=_default_project())
        sender = BroadcastSender(context)
        results = sender.send_batch([])

        assert results == []
        mock_post.assert_not_called()
