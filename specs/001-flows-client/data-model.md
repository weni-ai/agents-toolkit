# Data Model: Flows Client Abstraction

**Feature**: 001-flows-client | **Date**: 2026-06-10

This feature has no persistent storage; the "data model" is the set of in-memory entities that make up the client.

## FlowsClient

The abstraction owning configuration resolution, request construction, execution, and error translation.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `context` | `Context` | constructor argument | Existing immutable toolkit context (`weni.context.Context`) |
| `base_url` | `str` | context/env/default, normalized | Trailing slash stripped; default `https://flows.stg.cloud.weni.ai` |
| `auth_token` | `str` | `context.project["auth_token"]` | Required; missing token raises `FlowsClientConfigError` at construction (fail fast) |
| `project_uuid` | `str \| None` | context/env | Optional project identification |

**Lifecycle**: stateless after construction; one instance per tool execution. All configuration is resolved eagerly in `__init__`; requests never mutate client state.

**Validation rules** (from FR-003, FR-004, FR-005):

- Base URL: resolved with precedence `context.project` → `context.credentials` → `context.globals` → env var → default; normalized so `base_url + path` never produces duplicate or missing slashes.
- Auth token: must resolve to a non-empty value or construction fails with a configuration error naming the key and its expected sources.
- Optional values resolve to `None` without error.

## Configuration resolution (value object behavior)

| Value | Context keys (priority order) | Env var fallback | Required | Default |
|---|---|---|---|---|
| Base URL | `flows_url` in project → credentials → globals | `FLOWS_BASE_URL` | No | `https://flows.stg.cloud.weni.ai` |
| Auth token | `auth_token` in project | — | Yes | — |
| Project UUID | `uuid` in project → credentials → globals | `PROJECT_UUID` | No | `None` |

## Error hierarchy

```text
FlowsClientError (base — single catch point, FR-008)
├── FlowsClientConfigError   # missing/invalid configuration (FR-005)
├── FlowsHTTPError           # non-2xx response (FR-006)
├── FlowsNetworkError        # transport failure, no response received (FR-007)
└── FlowsResponseError       # 2xx with malformed non-empty body (edge case)
```

| Error | Carried data |
|---|---|
| `FlowsClientConfigError` | message naming the missing key and its expected sources |
| `FlowsHTTPError` | `status_code: int`, `response_body: str` |
| `FlowsNetworkError` | message describing the transport failure; original exception chained |
| `FlowsResponseError` | message indicating the response body was unreadable |

## Request/response (transient values)

| Value | Type | Notes |
|---|---|---|
| Method | `str` | One of GET, POST, PUT, PATCH, DELETE (FR-002) |
| Path | `str` | Endpoint-agnostic, supplied by the caller (FR-001) |
| JSON payload | `dict[str, Any] \| None` | Optional; requests without a body supported |
| Query params | `dict[str, Any] \| None` | Optional |
| Headers | `dict[str, str]` | `Content-Type: application/json` + `Authorization: Bearer <token>` |
| Parsed response | `dict[str, Any] \| list[Any] \| None` | `None` for empty-body success (clarification Q4) |

## State transitions

None — the client is stateless and each request is independent. No retries, no connection pooling configuration, no timeout (clarification Q3).
