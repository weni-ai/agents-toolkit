"""
Tests for BaseResource.
"""

import pytest

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

    def test_get_headers_with_content_type(self, resource):
        """Test _get_headers with include_content_type=True."""
        headers = resource._get_headers(include_content_type=True)

        assert headers["Authorization"] == "Bearer test-jwt"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_get_headers_without_content_type(self, resource):
        """Test _get_headers with include_content_type=False."""
        headers = resource._get_headers(include_content_type=False)

        assert headers["Authorization"] == "Bearer test-jwt"
        assert "Content-Type" not in headers
        assert headers["Accept"] == "application/json"

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

    def test_handle_success_response(self, resource, mocker):
        """Test handling successful response."""
        response = mocker.MagicMock()
        response.ok = True
        response.content = b'{"data": "test"}'
        response.json.return_value = {"data": "test"}

        result = resource._handle_response(response)

        assert result == {"data": "test"}

    def test_handle_empty_success_response(self, resource, mocker):
        """Test handling empty successful response."""
        response = mocker.MagicMock()
        response.ok = True
        response.content = b""

        result = resource._handle_response(response)

        assert result == {}

    def test_handle_401_response(self, resource, mocker):
        """Test handling 401 response raises FlowsAuthenticationError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 401
        response.content = b'{"error": "Unauthorized"}'
        response.json.return_value = {"error": "Unauthorized"}

        with pytest.raises(FlowsAuthenticationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 401
        assert "Unauthorized" in str(exc_info.value)

    def test_handle_403_response(self, resource, mocker):
        """Test handling 403 response raises FlowsAuthenticationError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 403
        response.content = b'{"error": "Forbidden"}'
        response.json.return_value = {"error": "Forbidden"}

        with pytest.raises(FlowsAuthenticationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 403

    def test_handle_404_response(self, resource, mocker):
        """Test handling 404 response raises FlowsNotFoundError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 404
        response.content = b'{"error": "Not found"}'
        response.json.return_value = {"error": "Not found"}

        with pytest.raises(FlowsNotFoundError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 404

    def test_handle_400_response(self, resource, mocker):
        """Test handling 400 response raises FlowsValidationError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 400
        response.content = b'{"error": "Invalid data"}'
        response.json.return_value = {"error": "Invalid data"}

        with pytest.raises(FlowsValidationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 400

    def test_handle_500_response(self, resource, mocker):
        """Test handling 500 response raises FlowsServerError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 500
        response.content = b'{"error": "Server error"}'
        response.json.return_value = {"error": "Server error"}

        with pytest.raises(FlowsServerError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 500

    def test_handle_other_error_response(self, resource, mocker):
        """Test handling other error response raises FlowsAPIError."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 429
        response.content = b'{"error": "Rate limited"}'
        response.json.return_value = {"error": "Rate limited"}

        with pytest.raises(FlowsAPIError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 429

    def test_handle_error_response_with_json_array(self, resource, mocker):
        """Test handling error response with JSON array doesn't crash."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 400
        response.content = b'["error1", "error2"]'
        response.json.return_value = ["error1", "error2"]

        with pytest.raises(FlowsValidationError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 400
        assert "error1" in str(exc_info.value)

    def test_handle_error_response_with_json_string(self, resource, mocker):
        """Test handling error response with JSON string doesn't crash."""
        response = mocker.MagicMock()
        response.ok = False
        response.status_code = 500
        response.content = b'"Internal server error"'
        response.json.return_value = "Internal server error"

        with pytest.raises(FlowsServerError) as exc_info:
            resource._handle_response(response)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value)


class TestBaseResourceHTTPMethods:
    """Tests for BaseResource HTTP methods."""

    @pytest.fixture
    def resource(self):
        """Create a BaseResource for testing."""
        client = FlowsClient(base_url="https://flows.weni.ai", jwt_token="test-jwt")
        return BaseResource(client)

    def test_get_request(self, resource, mocker):
        """Test _get makes correct request."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"data": "test"}'
        mock_response.json.return_value = {"data": "test"}

        mock_get = mocker.patch("weni.flows.resources.base.requests.get", return_value=mock_response)

        result = resource._get("/api/test", params={"key": "value"})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://flows.weni.ai/api/test" in call_args[0]
        assert call_args[1]["params"] == {"key": "value"}
        assert result == {"data": "test"}

    def test_post_request_with_json_data(self, resource, mocker):
        """Test _post with json_data includes Content-Type: application/json."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"created": true}'
        mock_response.json.return_value = {"created": True}

        mock_request = mocker.patch("weni.flows.resources.base.requests.request", return_value=mock_response)

        result = resource._post("/api/test", json_data={"name": "test"})

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]["json"] == {"name": "test"}
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        assert result == {"created": True}

    def test_post_request_with_form_data(self, resource, mocker):
        """Test _post with data does NOT include Content-Type header."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"created": true}'
        mock_response.json.return_value = {"created": True}

        mock_request = mocker.patch("weni.flows.resources.base.requests.request", return_value=mock_response)

        result = resource._post("/api/test", data={"name": "test"})

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]["data"] == {"name": "test"}
        # Content-Type should NOT be in headers when sending form data
        # This allows requests to set the correct Content-Type automatically
        assert "Content-Type" not in call_args[1]["headers"]
        assert call_args[1]["headers"]["Accept"] == "application/json"
        assert result == {"created": True}

    def test_patch_request_with_json_data(self, resource, mocker):
        """Test _patch with json_data includes Content-Type: application/json."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}

        mock_request = mocker.patch("weni.flows.resources.base.requests.request", return_value=mock_response)

        result = resource._patch("/api/test", json_data={"name": "updated"})

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        assert result == {"updated": True}

    def test_patch_request_with_form_data(self, resource, mocker):
        """Test _patch with data does NOT include Content-Type header."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b'{"updated": true}'
        mock_response.json.return_value = {"updated": True}

        mock_request = mocker.patch("weni.flows.resources.base.requests.request", return_value=mock_response)

        result = resource._patch("/api/test", data={"name": "updated"})

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[1]["data"] == {"name": "updated"}
        # Content-Type should NOT be in headers when sending form data
        assert "Content-Type" not in call_args[1]["headers"]
        assert call_args[1]["headers"]["Accept"] == "application/json"
        assert result == {"updated": True}

    def test_delete_request(self, resource, mocker):
        """Test _delete makes correct request."""
        mock_response = mocker.MagicMock()
        mock_response.ok = True
        mock_response.content = b"{}"
        mock_response.json.return_value = {}

        mock_delete = mocker.patch("weni.flows.resources.base.requests.delete", return_value=mock_response)

        result = resource._delete("/api/test")

        mock_delete.assert_called_once()
        assert result == {}
