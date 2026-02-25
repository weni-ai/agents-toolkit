"""
SQS-based broadcast sender.

This module provides the functionality to send broadcast messages
to an SQS queue for asynchronous processing by a Flows worker.

Supports both standard and FIFO queues. FIFO queues are automatically
detected by the .fifo suffix in the queue URL.
"""

import json
import os
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError

from weni.context import Context


class BroadcastSenderError(Exception):
    """Raised when there's an error sending a broadcast to SQS."""

    pass


class BroadcastSenderConfigError(BroadcastSenderError):
    """Raised when the sender is not properly configured."""

    pass


class BroadcastSender:
    """
    Sends broadcast messages to an SQS queue for asynchronous processing.

    The sender extracts configuration from the Context and environment variables,
    builds the payload expected by the Flows worker, and sends it to SQS.

    Configuration priority:
        1. context.project
        2. context.credentials
        3. context.globals
        4. Environment variables

    Required configuration:
        - SQS Queue URL: `sqs_queue_url` or `BROADCAST_SQS_QUEUE_URL` env var
        - Flows URL: `flows_url` or `FLOWS_BASE_URL` env var
        - JWT Token: `flows_jwt` or `jwt` in context

    Example:
        ```python
        from weni.broadcasts import BroadcastSender, Text

        sender = BroadcastSender(context)
        sender.send(Text(text="Hello!"))
        ```
    """

    def __init__(self, context: Context, sqs_client: Any = None):
        """
        Initialize the BroadcastSender.

        Args:
            context: The execution context containing configuration.
            sqs_client: Optional boto3 SQS client (for testing/mocking).
        """
        self.context = context
        self._sqs_client = sqs_client

        # Extract configuration
        self.queue_url = self._get_config("sqs_queue_url", "BROADCAST_SQS_QUEUE_URL")
        self.flows_url = self._get_config("flows_url", "FLOWS_BASE_URL")
        self.jwt_token = self._get_jwt_token()
        self.project_uuid = self._get_config("project_uuid", "PROJECT_UUID", required=False)

        # Detect FIFO queue by URL suffix
        self.is_fifo = self.queue_url.endswith(".fifo")

    def _get_config(self, key: str, env_var: str, required: bool = True) -> str | None:
        """
        Get a configuration value from context or environment.

        Priority: project > credentials > globals > environment

        Args:
            key: The key to look for in context mappings.
            env_var: The environment variable name as fallback.
            required: Whether to raise an error if not found.

        Returns:
            The configuration value or None if not required and not found.

        Raises:
            BroadcastSenderConfigError: If required and not found.
        """
        value = (
            self.context.project.get(key)
            or self.context.credentials.get(key)
            or self.context.globals.get(key)
            or os.environ.get(env_var)
        )

        if required and not value:
            raise BroadcastSenderConfigError(
                f"Missing required configuration: '{key}' not found in context "
                f"and '{env_var}' environment variable not set."
            )

        return value

    def _get_jwt_token(self) -> str | None:
        """
        Get the JWT token from context.

        Looks for 'flows_jwt' or 'jwt' in project/credentials.

        Returns:
            The JWT token or None if not found.
        """
        return (
            self.context.project.get("flows_jwt")
            or self.context.credentials.get("flows_jwt")
            or self.context.project.get("jwt")
            or self.context.credentials.get("jwt")
        )

    def _get_contact_urn(self) -> str | None:
        """
        Get the contact URN from context.

        Returns:
            The contact URN or None if not available.
        """
        urns = self.context.contact.get("urns")
        if urns and isinstance(urns, (list, tuple)) and len(urns) > 0:
            return urns[0]
        return self.context.contact.get("urn")

    @property
    def sqs_client(self):
        """Lazy-loaded SQS client."""
        if self._sqs_client is None:
            self._sqs_client = boto3.client("sqs")
        return self._sqs_client

    def _get_message_group_id(self) -> str:
        """
        Get the MessageGroupId for FIFO queues.

        Uses project_uuid if available, otherwise uses a default group.
        This ensures messages for the same project are processed in order.

        Returns:
            The MessageGroupId string.
        """
        return self.project_uuid or "default-broadcast-group"

    def _generate_deduplication_id(self) -> str:
        """
        Generate a unique MessageDeduplicationId for FIFO queues.

        Uses UUID4 to ensure each message is unique and processed.

        Returns:
            A unique deduplication ID.
        """
        return str(uuid.uuid4())

    def build_payload(self, message_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Build the full SQS message payload.

        The payload contains all information needed by the Flows worker
        to make the HTTP request to the WhatsApp Broadcasts endpoint.

        Args:
            message_payload: The formatted message from Message.format_message().

        Returns:
            The complete payload for the SQS message.
        """
        contact_urn = self._get_contact_urn()

        payload: dict[str, Any] = {
            "msg": message_payload,
            "flows_url": self.flows_url,
        }

        # Add URN if available
        if contact_urn:
            payload["urns"] = [contact_urn]

        # Add JWT token if available
        if self.jwt_token:
            payload["jwt_token"] = self.jwt_token

        # Add project UUID if available
        if self.project_uuid:
            payload["project_uuid"] = self.project_uuid

        return payload

    def send(self, message_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send a message payload to the SQS queue.

        For FIFO queues, automatically includes MessageGroupId and
        MessageDeduplicationId to ensure proper ordering and deduplication.

        Args:
            message_payload: The formatted message from Message.format_message().

        Returns:
            The SQS SendMessage response.

        Raises:
            BroadcastSenderError: If sending fails.
        """
        payload = self.build_payload(message_payload)

        send_kwargs: dict[str, Any] = {
            "QueueUrl": self.queue_url,
            "MessageBody": json.dumps(payload),
        }

        # Add FIFO-specific parameters
        if self.is_fifo:
            send_kwargs["MessageGroupId"] = self._get_message_group_id()
            send_kwargs["MessageDeduplicationId"] = self._generate_deduplication_id()

        try:
            response = self.sqs_client.send_message(**send_kwargs)
            return response
        except ClientError as e:
            raise BroadcastSenderError(f"Failed to send message to SQS: {e}") from e

    def send_batch(self, message_payloads: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Send multiple message payloads to the SQS queue in a batch.

        For FIFO queues, automatically includes MessageGroupId and
        MessageDeduplicationId for each entry.

        Args:
            message_payloads: List of formatted messages.

        Returns:
            The SQS SendMessageBatch response.

        Raises:
            BroadcastSenderError: If sending fails.
        """
        if not message_payloads:
            return {"Successful": [], "Failed": []}

        entries = []
        for i, msg_payload in enumerate(message_payloads):
            payload = self.build_payload(msg_payload)
            entry: dict[str, Any] = {
                "Id": str(i),
                "MessageBody": json.dumps(payload),
            }

            # Add FIFO-specific parameters
            if self.is_fifo:
                entry["MessageGroupId"] = self._get_message_group_id()
                entry["MessageDeduplicationId"] = self._generate_deduplication_id()

            entries.append(entry)

        try:
            response = self.sqs_client.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=entries,
            )
            return response
        except ClientError as e:
            raise BroadcastSenderError(f"Failed to send batch to SQS: {e}") from e
