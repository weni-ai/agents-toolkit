# Public API Contract: `weni.flows`

**Feature**: 001-flows-client | **Date**: 2026-06-10

This is the contract the library exposes to toolkit developers. It is the surface that must remain stable; internals may change freely.

## Imports

```python
from weni.flows import (
	FlowsClient,
	FlowsClientError,
	FlowsClientConfigError,
	FlowsHTTPError,
	FlowsNetworkError,
	FlowsResponseError,
)
```

## `FlowsClient`

### Construction

```python
client = FlowsClient(context)
```

- `context: weni.context.Context` — the execution context of the current tool.
- Resolves configuration eagerly (see [data-model.md](../data-model.md) for precedence table).
- **Raises** `FlowsClientConfigError` if the auth token cannot be resolved. No request is ever sent unauthenticated.

### Request methods

```python
client.get(path, params=None)
client.post(path, json=None, params=None)
client.put(path, json=None, params=None)
client.patch(path, json=None, params=None)
client.delete(path, params=None)
```

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` | Endpoint path relative to the base URL (e.g. `'/api/v2/whatsapp_broadcasts.json'`). Leading slash optional — the client normalizes. |
| `json` | `dict[str, Any] \| None` | Optional JSON body. |
| `params` | `dict[str, Any] \| None` | Optional query string parameters. |

**Returns**: parsed JSON response (`dict[str, Any] | list[Any]`), or `None` when the response is a success with an empty body (e.g. 204).

**Guarantees**:

- Full URL = normalized base URL + normalized path; never duplicate or missing slashes.
- Headers always include `Content-Type: application/json` and `Authorization: Bearer <token>`.
- No knowledge of any specific Flows endpoint lives in the client.
- No timeout is imposed.

**Raises**:

| Error | When |
|---|---|
| `FlowsHTTPError` | Flows responded with a non-2xx status. Exposes `status_code` and `response_body`. |
| `FlowsNetworkError` | The request failed before a response was received (DNS, connection, etc.). |
| `FlowsResponseError` | Success status but a non-empty body that cannot be parsed as JSON. |

## Error hierarchy contract

- All errors subclass `FlowsClientError`; `except FlowsClientError` catches every failure mode (configuration, HTTP, network, response parsing).
- `FlowsHTTPError.status_code: int` and `FlowsHTTPError.response_body: str` are part of the public contract.
- Original transport exceptions are chained (`raise ... from ...`) for diagnostics but are not part of the contract.

## Compatibility

- Python >= 3.10; fully type-annotated; mypy-clean.
- Synchronous only.
- New MINOR version of `weni-agents-toolkit` (backwards-compatible addition); `CHANGELOG.md` entry required.
- Not re-exported from the root `weni` package in this iteration (see research.md R6).
