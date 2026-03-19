"""
HTTP-based broadcast sender.

Sends broadcast messages directly to the Flows WhatsApp Broadcasts API
via HTTP POST during tool execution.
"""

import os
from typing import Any

import requests

from weni.context import Context


class BroadcastSenderError(Exception):
    """Raised when there's an error sending a broadcast."""

    pass


class BroadcastSenderConfigError(BroadcastSenderError):
    """Raised when the sender is not properly configured."""

    pass


class BroadcastSender:
    """
    Sends broadcast messages directly to the Flows WhatsApp Broadcasts API.

    The sender extracts configuration from the Context and environment variables,
    builds the request payload, and POSTs to the Flows API.

    Configuration priority:
        1. context.project
        2. context.credentials
        3. context.globals
        4. Environment variables

    Required configuration:
        - Flows URL: `flows_url` or `FLOWS_BASE_URL` env var
        - Auth Token: `auth_token` in context.project

    Optional configuration:
        - Channel UUID: `channel_uuid` or `BROADCAST_CHANNEL_UUID` env var
    """

    BROADCASTS_PATH = "/api/v2/internals/whatsapp_broadcasts"
    DEFAULT_FLOWS_URL = "https://flows.stg.cloud.weni.ai"

    def __init__(self, context: Context):
        self.context = context

        flows_url = self._get_config("flows_url", "FLOWS_BASE_URL", required=False) or self.DEFAULT_FLOWS_URL
        self.flows_url: str = flows_url.rstrip("/")

        self.auth_token = self._get_auth_token()
        self.project_uuid = self._get_config("uuid", "PROJECT_UUID", required=False)
        self.channel_uuid = self._get_config("channel_uuid", "BROADCAST_CHANNEL_UUID", required=False)

    def _get_config(self, key: str, env_var: str, required: bool = True) -> str | None:
        """
        Get a configuration value from context or environment.

        Priority: project > credentials > globals > environment
        """
        value = (
            self.context.project.get(key)
            or self.context.credentials.get(key)
            or self.context.contact.get(key)
            or self.context.globals.get(key)
            or os.environ.get(env_var)
        )

        if required and not value:
            raise BroadcastSenderConfigError(
                f"Missing required configuration: '{key}' not found in context "
                f"and '{env_var}' environment variable not set."
            )

        return value

    def _get_auth_token(self) -> str | None:
        """Get the auth token from context.project."""
        return self.context.project.get("auth_token")

    def _get_contact_urn(self) -> str | None:
        """
        Get the contact URN from context.

        Priority: contact.urns > contact.urn > parameters.contact_urn
        """
        urns = self.context.contact.get("urns")
        if urns and isinstance(urns, (list, tuple)) and len(urns) > 0:
            return urns[0]
        return self.context.contact.get("urn") or self.context.parameters.get("contact_urn")

    def _build_url(self) -> str:
        return f"{self.flows_url}{self.BROADCASTS_PATH}"

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Token {self.auth_token}"
        return headers

    def _build_request_body(self, message_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Build the JSON body for the Flows WhatsApp Broadcasts API.

        Args:
            message_payload: The formatted message from Message.format_message().

        Returns:
            The request body dict.
        """
        contact_urn = self._get_contact_urn()

        body: dict[str, Any] = {"msg": message_payload}

        if contact_urn:
            body["urns"] = [contact_urn]

        if self.channel_uuid:
            body["channel"] = self.channel_uuid

        return body

    def send(self, message_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send a broadcast message via HTTP POST to the Flows API.

        Args:
            message_payload: The formatted message from Message.format_message().

        Returns:
            The parsed JSON response from Flows.

        Raises:
            BroadcastSenderError: If the request fails or returns non-2xx.
        """
        url = self._build_url()
        headers = self._build_headers()
        body = self._build_request_body(message_payload)

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise BroadcastSenderError(
                f"Flows API returned {e.response.status_code}: {e.response.text}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise BroadcastSenderError(f"Failed to send broadcast: {e}") from e

    def send_batch(self, message_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Send multiple broadcast messages sequentially.

        Args:
            message_payloads: List of formatted messages.

        Returns:
            List of JSON responses from Flows.
        """
        results = []
        for payload in message_payloads:
            results.append(self.send(payload))
        return results
