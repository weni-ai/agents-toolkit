"""
Weni Flows Client

A base client for integrating with the Weni Flows API.
Provides the foundation for building API integrations.
"""

from weni.flows.client import FlowsClient
from weni.flows.exceptions import (
    FlowsAPIError,
    FlowsAuthenticationError,
    FlowsConfigurationError,
    FlowsNotFoundError,
    FlowsServerError,
    FlowsValidationError,
)
from weni.flows.resources.base import BaseResource

__all__ = [
    "FlowsClient",
    "BaseResource",
    "FlowsAPIError",
    "FlowsAuthenticationError",
    "FlowsConfigurationError",
    "FlowsNotFoundError",
    "FlowsServerError",
    "FlowsValidationError",
]
