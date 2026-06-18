# Flows Client

The `weni.flows` package provides `FlowsClient`, a reusable HTTP client for the Flows platform. It abstracts URL building, configuration resolution, authentication headers, and error translation, so toolkit integrations don't need to hand-roll request plumbing.

The client is endpoint-agnostic: you provide the endpoint path and payload, it handles the rest.

## Usage

```python
from weni.flows import FlowsClient

client = FlowsClient(context)

# GET with query parameters
result = client.get("/api/v2/contacts.json", params={"page": 2})

# POST with a JSON body
result = client.post("/api/v2/messages.json", json={"text": "Hello"})

# PUT, PATCH, and DELETE are also available
client.put("/api/v2/things/1.json", json={"name": "Updated"})
client.patch("/api/v2/things/1.json", json={"name": "Patched"})
client.delete("/api/v2/things/1.json")
```

All methods return the parsed JSON response (`dict` or `list`), or `None` when the response is a success with an empty body (e.g. `204 No Content`).

## Configuration

Configuration is resolved eagerly when the client is constructed, with the following precedence:

| Value | Context keys (priority order) | Environment fallback | Required | Default |
|---|---|---|---|---|
| Base URL | `flows_url` in `project` → `credentials` → `globals` | `FLOWS_BASE_URL` | No | `https://flows.stg.cloud.weni.ai` |
| Auth token | `auth_token` in `project` | — | Yes | — |
| Project UUID | `uuid` in `project` → `credentials` → `globals` | `PROJECT_UUID` | No | `None` |

If the auth token cannot be resolved, the constructor raises `FlowsClientConfigError` immediately — the client never sends unauthenticated requests.

Every request includes the headers `Content-Type: application/json` and `Authorization: Bearer <token>`.

## Error handling

All failures are raised as subclasses of `FlowsClientError`, so a single catch covers every failure mode:

```python
from weni.flows import (
    FlowsClient,
    FlowsClientError,
    FlowsClientConfigError,
    FlowsHTTPError,
    FlowsNetworkError,
    FlowsResponseError,
)

try:
    result = client.post("/api/v2/messages.json", json={"text": "Hello"})
except FlowsHTTPError as e:
    # Flows responded with a non-success status
    print(e.status_code, e.response_body)
except FlowsNetworkError:
    # The request failed before a response was received
    ...
except FlowsClientError:
    # Catches every client failure mode (config, HTTP, network, parsing)
    ...
```

| Error | Raised when |
|---|---|
| `FlowsClientConfigError` | A required configuration value is missing (at construction) |
| `FlowsHTTPError` | Flows responds with a non-2xx status — exposes `status_code` and `response_body` |
| `FlowsNetworkError` | The request fails before a response is received (DNS, connection, etc.) |
| `FlowsResponseError` | A success response carries a non-empty body that cannot be parsed as JSON |
