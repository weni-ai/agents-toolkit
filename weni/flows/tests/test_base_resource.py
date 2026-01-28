"""
Tests for BaseResource.
"""

import pytest
from unittest.mock import MagicMock, patch

from weni.flows import FlowsClient
from weni.flows.resources.base import BaseResource
from weni.flows.exceptions import (
    FlowsAPIError,
    FlowsAuthenticationError,
    FlowsNotFoundError,
    FlowsServerError,
    FlowsValidationError,
)


class TestBaseResource:
    """Tests for BaseResource."""

    @pytest.fixture
    def client(self):
        """Create a FlowsClient for testing."""
        return FlowsClient(
            base_url="https://flows.weni.ai",
            jwt_token="test-jwt",
        )

    @pytest.fixture
    def resource(self, client):
        """Create a BaseResource for testing."""
        return BaseResource(client)

    def test_base_url_property(self, resource, client):
        """Test _base_url property."""
        assert resource._base_url == client.base_url

    def test_headers_with_jwt(self, resource):
        """Test _headers includes JWT token."""
        headers = resource._headers

        assert headers["Authorization"] == "Bearer test-jwt"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_headers_without_jwt(self, client):
        """Test _headers without JWT token."""
        client.jwt_token = None
        resource = BaseResource(client)
        headers = resource._headers

        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_build_url(self, resource):
        """Test URL building."""
        url = resource._build_url("/api/v2/contacts")
        assert url == "https://flows.weni.ai/api/v2/contacts"

    def test_build_url_strips_slashes(self, resource):
        """Test URL building strips extra slashes."""
        url = resource._build_url("api/v2/contacts")
        assert url == "https://flows.weni.ai/api/v2/contacts"


class TestBaseResourceHandleResponse:
    """Tests for BaseResource._handle_response()."""

    @pytest.fixture
    def resource(self):
        """Create a BaseResource for testing."""
        client = FlowsClient(base_url="https://flows.weni.ai")
        return BaseResource(client)

    def test_handle_success_response(self, resource):
        """Test handling successful response."""
        response = MagicMock()
        response.ok = True
        response.content = b'{"data": "test"}'
        response.json.return_value = {"data": "test"}

        result = resource._handle_response(response)

        assert result == {"data": "test"}

    def test_handle_empty_success_response(self, resource):
        """Test handling empty successful response."""
        response = MagicMock()
        response.ok = True
        response.content = b""

        result = resource._handle_response(response)

        assert result == {}

    def test_handle_401_response(self, resource):
        """Test handling 401 response raises FlowsAuthenticationError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 401
        response.content = b'{"error": "Unauthorized"}'
        response.json.return_value = {"error": "Unauthorized"}

        with pytest.raises(FlowsAuthenticationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 401
        assert "Unauthorized" in str(exc_info.value)

    def test_handle_403_response(self, resource):
        """Test handling 403 response raises FlowsAuthenticationError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 403
        response.content = b'{"error": "Forbidden"}'
        response.json.return_value = {"error": "Forbidden"}

        with pytest.raises(FlowsAuthenticationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 403

    def test_handle_404_response(self, resource):
        """Test handling 404 response raises FlowsNotFoundError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 404
        response.content = b'{"error": "Not found"}'
        response.json.return_value = {"error": "Not found"}

        with pytest.raises(FlowsNotFoundError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 404

    def test_handle_400_response(self, resource):
        """Test handling 400 response raises FlowsValidationError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 400
        response.content = b'{"error": "Invalid data"}'
        response.json.return_value = {"error": "Invalid data"}

        with pytest.raises(FlowsValidationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 400

    def test_handle_500_response(self, resource):
        """Test handling 500 response raises FlowsServerError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 500
        response.content = b'{"error": "Server error"}'
        response.json.return_value = {"error": "Server error"}

        with pytest.raises(FlowsServerError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 500

    def test_handle_other_error_response(self, resource):
        """Test handling other error response raises FlowsAPIError."""
        response = MagicMock()
        response.ok = False
        response.status_code = 429
        response.content = b'{"error": "Rate limited"}'
        response.json.return_value = {"error": "Rate limited"}

        with pytest.raises(FlowsAPIError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 429


class TestBaseResourceHTTPMethods:
    """Tests for BaseResource HTTP methods."""

    @pytest.fixture
    def resource(self):
        """Create a BaseResource for testing."""
        client = FlowsClient(base_url="https://flows.weni.ai", jwt_token="test-jwt")
        return BaseResource(client)

    @patch("weni.flows.resources.base.requests.get")
    def test_get_request(self, mock_get, resource):
        """Test _get makes correct request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = resource._get("/api/test", params={"key": "value"})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://flows.weni.ai/api/test" in call_args[0]
        assert call_args[1]["params"] == {"key": "value"}
        assert result == {"data": "test"}

    @patch("weni.flows.resources.base.requests.post")
    def test_post_request(self, mock_post, resource):
        """Test _post makes correct request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"created": true}'
        mock_response.json.return_value = {"created": True}
        mock_post.return_value = mock_response

        result = resource._post("/api/test", json_data={"name": "test"})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"] == {"name": "test"}
        assert result == {"created": True}

    @patch("weni.flows.resources.base.requests.patch")
    def test_patch_request(self, mock_patch, resource):
        """Test _patch makes correct request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}
        mock_patch.return_value = mock_response

        result = resource._patch("/api/test", json_data={"name": "updated"})

        mock_patch.assert_called_once()
        assert result == {"updated": True}

    @patch("weni.flows.resources.base.requests.delete")
    def test_delete_request(self, mock_delete, resource):
        """Test _delete makes correct request."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b"{}"
        mock_response.json.return_value = {}
        mock_delete.return_value = mock_response

        result = resource._delete("/api/test")

        mock_delete.assert_called_once()
        assert result == {}
