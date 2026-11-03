"""
Broadcast integration: a real Tool, the real sender, and a mocked HTTP call.

The body posted to Flows and the messages_sent log must match the golden
payload, with custom_data nested inside msg when it is provided.
"""

from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

import weni  # noqa: F401  -- registers the broadcasts facade on Tool
from weni.broadcasts.messages import Text
from weni.broadcasts.tests.golden_payloads import GOLDEN_CASES
from weni.context import Context
from weni.responses import FinalResponse
from weni.tool import Tool

CURL_CUSTOM_DATA = {
    "order_id": "1234567890-01",
    "coupon": {"code": "BLACKFRIDAY10", "expires_at": "2026-11-30T23:59:59Z"},
    "tags": ["vip", "recovery"],
}

EXPECTED_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-token",
}


def _context() -> Context:
    return Context(
        credentials={},
        parameters={},
        globals={},
        contact={"urns": ["whatsapp:5511999999999"]},
        project={
            "auth_token": "test-token",
            "channel_uuid": "ch-123",
            "flows_url": "https://flows.weni.ai",
        },
        constants={},
    )


def _mock_response() -> MagicMock:
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"id": 1}
    response.raise_for_status.return_value = None
    return response


def _body(message_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "msg": message_payload,
        "urns": ["whatsapp:5511999999999"],
        "channel": "ch-123",
    }


def _run(send: Any) -> dict[str, Any]:
    class SendingTool(Tool):
        def execute(self, context: Context):
            send(self)
            return FinalResponse()

    result, _format, _events, _traces = cast(tuple, SendingTool(_context()))
    return result


class TestBroadcastIntegration:
    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda case: case.name)
    @patch("weni.broadcasts.sender.requests.post")
    def test_send_broadcast_without_custom_data(self, mock_post, case):
        mock_post.return_value = _mock_response()

        result = _run(lambda tool: tool.send_broadcast(case.build_min()))

        assert result["messages_sent"] == [case.expected_min]
        mock_post.assert_called_once_with(
            "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
            headers=EXPECTED_HEADERS,
            json=_body(case.expected_min),
        )
        body = mock_post.call_args.kwargs["json"]
        assert "custom_data" not in body
        assert "custom_data" not in body["msg"]

    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda case: case.name)
    @patch("weni.broadcasts.sender.requests.post")
    def test_send_broadcast_nests_custom_data_inside_msg(self, mock_post, case):
        mock_post.return_value = _mock_response()
        expected = {**case.expected_min, "custom_data": CURL_CUSTOM_DATA}

        result = _run(lambda tool: tool.send_broadcast(case.build_min(custom_data=CURL_CUSTOM_DATA)))

        assert result["messages_sent"] == [expected]
        body = mock_post.call_args.kwargs["json"]
        assert body == _body(expected)
        assert "custom_data" not in body
        assert body["msg"]["custom_data"] == CURL_CUSTOM_DATA

    @patch("weni.broadcasts.sender.requests.post")
    def test_broadcasts_send_posts_the_same_body(self, mock_post):
        mock_post.return_value = _mock_response()
        message = Text(text="Hello", custom_data={"a": 1})

        result = _run(lambda tool: tool.broadcasts.send(message))

        expected = {"text": "Hello", "custom_data": {"a": 1}}
        assert result["messages_sent"] == [expected]
        mock_post.assert_called_once_with(
            "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
            headers=EXPECTED_HEADERS,
            json=_body(expected),
        )

    @patch("weni.broadcasts.sender.requests.post")
    def test_send_many_posts_each_message(self, mock_post):
        mock_post.return_value = _mock_response()
        messages = [Text(text="Hello"), Text(text="Hello", custom_data={"a": 1})]

        result = _run(lambda tool: tool.broadcasts.send_many(messages))

        first = {"text": "Hello"}
        second = {"text": "Hello", "custom_data": {"a": 1}}
        assert result["messages_sent"] == [first, second]
        assert mock_post.call_count == 2
        bodies = [call.kwargs["json"] for call in mock_post.call_args_list]
        assert bodies == [_body(first), _body(second)]
        assert "custom_data" not in bodies[0]["msg"]
        assert bodies[1]["msg"]["custom_data"] == {"a": 1}
