# Flows Integration

The `FlowsClient` provides the foundation for integrating tools with the Weni Flows API. It handles authentication and configuration management.

## How Authentication Works

The Flows API uses **JWT authentication** where the `project_uuid` is embedded **inside the JWT token itself**. When the Flows API receives a request, it:

1. Extracts the JWT token from the `Authorization: Bearer <token>` header
2. Decodes the token and extracts the `project_uuid` from the payload
3. Uses that `project_uuid` for the request context

**This means you don't need to pass `project_uuid` as a parameter** - it's already in the JWT!

## Quick Start

```python
from weni.flows import FlowsClient

# Initialize from context
flows = FlowsClient.from_context(context)

# Or directly
flows = FlowsClient(
    base_url="https://flows.weni.ai",
    jwt_token="your-jwt-token"  # Contains project_uuid in payload
)
```

## Configuration

### From Context (Recommended)

```python
flows = FlowsClient.from_context(context)
```

The client extracts configuration from the context:

| Config | Source Priority |
|--------|-----------------|
| `base_url` | `project.flows_url` → `credentials.flows_url` → `globals.flows_url` |
| `jwt_token` | `project.flows_jwt` → `credentials.flows_jwt` → `project.jwt` → `credentials.jwt` |

### JWT Token Structure

The JWT token should have a payload like:

```json
{
  "project_uuid": "your-project-uuid",
  "email": "user@example.com",
  "exp": 1234567890
}
```

## BaseResource

The `BaseResource` class provides the foundation for building API integrations with:

- Automatic JWT authentication
- Consistent error handling
- HTTP methods (GET, POST, PATCH, DELETE)

```python
from weni.flows import FlowsClient, BaseResource

class MyResource(BaseResource):
    def get_data(self):
        return self._get("/api/v2/my-endpoint")
    
    def create_data(self, data):
        return self._post("/api/v2/my-endpoint", json_data=data)
```

## Error Handling

The client raises specific exceptions:

```python
from weni.flows import (
    FlowsAPIError,
    FlowsAuthenticationError,
    FlowsNotFoundError,
    FlowsValidationError,
    FlowsConfigurationError,
)

try:
    # API call...
    pass
except FlowsValidationError as e:
    print(f"Invalid data: {e.message}")
except FlowsNotFoundError as e:
    print(f"Not found: {e.message}")
except FlowsAuthenticationError as e:
    print(f"Auth failed: {e.message}")
except FlowsAPIError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```
