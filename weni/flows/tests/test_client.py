"""
Tests for FlowsClient.
"""

import pytest

from weni.flows import FlowsClient
from weni.flows.exceptions import FlowsConfigurationError


class TestFlowsClientInit:
    """Tests for FlowsClient initialization."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        client = FlowsClient(base_url="https://flows.weni.ai")

        assert client.base_url == "https://flows.weni.ai"
        assert client.jwt_token is None

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        client = FlowsClient(
            base_url="https://flows.weni.ai",
            jwt_token="test-token",
        )

        assert client.base_url == "https://flows.weni.ai"
        assert client.jwt_token == "test-token"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url."""
        client = FlowsClient(base_url="https://flows.weni.ai/")

        assert client.base_url == "https://flows.weni.ai"

    def test_init_without_base_url_raises_error(self):
        """Test that missing base_url raises error."""
        with pytest.raises(FlowsConfigurationError, match="base_url is required"):
            FlowsClient(base_url="")


class TestFlowsClientFromContext:
    """Tests for FlowsClient.from_context()."""

    def test_from_context_with_project_flows_url(self, mocker):
        """Test creating client from context with flows_url in project."""
        context = mocker.MagicMock()
        context.project = {"flows_url": "https://flows.weni.ai", "flows_jwt": "test-jwt"}
        context.credentials = {}
        context.globals = {}

        client = FlowsClient.from_context(context)

        assert client.base_url == "https://flows.weni.ai"
        assert client.jwt_token == "test-jwt"

    def test_from_context_with_credentials_flows_url(self, mocker):
        """Test creating client from context with flows_url in credentials."""
        context = mocker.MagicMock()
        context.project = {}
        context.credentials = {"flows_url": "https://flows.weni.ai", "flows_jwt": "test-jwt"}
        context.globals = {}

        client = FlowsClient.from_context(context)

        assert client.base_url == "https://flows.weni.ai"
        assert client.jwt_token == "test-jwt"

    def test_from_context_with_globals_flows_url(self, mocker):
        """Test creating client from context with flows_url in globals."""
        context = mocker.MagicMock()
        context.project = {}
        context.credentials = {}
        context.globals = {"flows_url": "https://flows.weni.ai"}

        client = FlowsClient.from_context(context)

        assert client.base_url == "https://flows.weni.ai"

    def test_from_context_without_flows_url_raises_error(self, mocker):
        """Test that missing flows_url raises error."""
        context = mocker.MagicMock()
        context.project = {}
        context.credentials = {}
        context.globals = {}

        with pytest.raises(FlowsConfigurationError, match="Flows URL not found"):
            FlowsClient.from_context(context)

    def test_from_context_jwt_priority(self, mocker):
        """Test JWT extraction priority: project.flows_jwt > credentials.flows_jwt > project.jwt."""
        context = mocker.MagicMock()
        context.project = {
            "flows_url": "https://flows.weni.ai",
            "flows_jwt": "project-flows-jwt",
            "jwt": "project-jwt",
        }
        context.credentials = {"flows_jwt": "credentials-flows-jwt"}
        context.globals = {}

        client = FlowsClient.from_context(context)

        assert client.jwt_token == "project-flows-jwt"


class TestFlowsClientRepr:
    """Tests for FlowsClient string representation."""

    def test_repr(self):
        """Test string representation."""
        client = FlowsClient(base_url="https://flows.weni.ai")

        assert "FlowsClient" in repr(client)
        assert "flows.weni.ai" in repr(client)
