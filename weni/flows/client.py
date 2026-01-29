"""
Flows API Client.

Base client for integrating with the Weni Flows API.
"""

from typing import TYPE_CHECKING

from weni.flows.exceptions import FlowsConfigurationError

if TYPE_CHECKING:
    from weni.context import Context


class FlowsClient:
    """
    Base client for the Weni Flows API.

    Provides the foundation for building API integrations with proper
    authentication and configuration management.

    The client uses JWT authentication where the project_uuid is embedded
    inside the JWT token itself. The Flows API automatically extracts the
    project_uuid from the token.

    Example:
        ```python
        from weni.flows import FlowsClient

        # Initialize from context
        flows = FlowsClient.from_context(context)

        # Or directly
        flows = FlowsClient(
            base_url="https://flows.weni.ai",
            jwt_token="your-jwt-token"
        )
        ```
    """

    def __init__(
        self,
        base_url: str,
        jwt_token: str | None = None,
    ):
        """
        Initialize the Flows client.

        Args:
            base_url: Base URL for the Flows API (e.g., "https://flows.weni.ai").
            jwt_token: JWT token for authentication. The token should contain
                      'project_uuid' in its payload - the Flows API extracts it
                      automatically during authentication.
        """
        if not base_url:
            raise FlowsConfigurationError("base_url is required")

        self.base_url = base_url.rstrip("/")
        self.jwt_token = jwt_token

    @classmethod
    def from_context(cls, context: "Context") -> "FlowsClient":
        """
        Create a FlowsClient from a tool Context.

        The client will extract configuration from the context in this order:
        1. project.flows_url or credentials.flows_url or globals.flows_url -> base_url
        2. project.flows_jwt or credentials.flows_jwt or project.jwt -> jwt_token

        Note: The project_uuid does NOT need to be passed separately - it should
        be embedded inside the JWT token. The Flows API extracts it automatically
        when it decodes the token during authentication.

        Args:
            context: The tool execution context.

        Returns:
            Configured FlowsClient instance.

        Raises:
            FlowsConfigurationError: If required configuration is missing.
        """
        # Extract base URL
        base_url = (
            context.project.get("flows_url")
            or context.credentials.get("flows_url")
            or context.globals.get("flows_url")
        )
        if not base_url:
            raise FlowsConfigurationError(
                "Flows URL not found in context. " "Please configure 'flows_url' in project, credentials, or globals."
            )

        # Extract JWT token (contains project_uuid in its payload)
        jwt_token = (
            context.project.get("flows_jwt")
            or context.credentials.get("flows_jwt")
            or context.project.get("jwt")
            or context.credentials.get("jwt")
        )

        return cls(
            base_url=base_url,
            jwt_token=jwt_token,
        )

    def __repr__(self) -> str:
        return f"FlowsClient(base_url={self.base_url!r})"


__all__ = ["FlowsClient"]
