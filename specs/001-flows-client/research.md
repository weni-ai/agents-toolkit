# Research: Flows Client Abstraction

**Feature**: 001-flows-client | **Date**: 2026-06-10

No NEEDS CLARIFICATION markers remained in the Technical Context; the decisions below consolidate the choices that shape the design, grounded in the existing codebase and the spec clarifications.

## R1. Package location

- **Decision**: Implement the client as the `weni/flows/` subpackage (`client.py`, `exceptions.py`, `tests/`).
- **Rationale**: Constitution Principle V requires one subpackage per domain; the client's domain is the Flows platform. `weni/flows/` already exists as an empty placeholder (only an empty `resources/` dir, no code and no inbound references), so adopting it is non-breaking and matches the intended layout.
- **Alternatives considered**: `weni/clients/flows/` (rejected: introduces a new grouping level no other domain uses); a module inside `weni/broadcasts/` (rejected: spec forbids touching broadcasts and the client must be feature-agnostic).

## R2. HTTP library

- **Decision**: Use `requests`, the existing runtime dependency.
- **Rationale**: Already pinned in `pyproject.toml` and used by `weni/broadcasts/sender.py`; the client is synchronous per the spec assumption, and `types-requests` is already available for mypy.
- **Alternatives considered**: `httpx` (rejected: new dependency, async support out of scope); `urllib3` directly (rejected: lower-level, more code for no benefit).

## R3. Configuration resolution

- **Decision**: Resolve each configuration value with precedence `context.project` → `context.credentials` → `context.globals` → environment variable, with `https://flows.stg.cloud.weni.ai` as default base URL when none is provided. The auth token is resolved from `context.project["auth_token"]`. Missing required values raise `FlowsClientConfigError` naming the key and its expected sources at client construction time (fail fast, per clarification Q1).
- **Rationale**: Mirrors the precedence already established by `BroadcastSender._get_config` (minus `context.contact`, which holds contact data rather than client configuration), keeping behavior predictable for toolkit developers. Failing at construction surfaces misconfiguration before any request is attempted.
- **Alternatives considered**: Including `context.contact` in the lookup chain (rejected: contact data is per-conversation, not deployment configuration; its presence in the sender lookup is an artifact of that feature's needs); lazy validation at request time (rejected: clarification Q1 chose fail-fast).

## R4. Request surface

- **Decision**: A private generic `_request(method, path, ...)` plus public convenience methods `get`, `post`, `put`, `patch`, `delete` (per clarification Q2). Paths are joined to the normalized base URL (trailing slashes stripped, leading slash on the path ensured). JSON payloads are optional; query parameters supported via a `params` argument. No timeout is set (per clarification Q3).
- **Rationale**: Convenience methods keep call sites readable (`client.post('/api/v2/...', json=payload)`) while a single private executor centralizes header construction, URL building, and error translation.
- **Alternatives considered**: Only a generic `request(method, ...)` (rejected by clarification Q2 — per-verb conveniences chosen); per-endpoint methods (rejected: spec FR-001/FR-012 require endpoint-agnosticism).

## R5. Error hierarchy and response handling

- **Decision**: `FlowsClientError` (base) with subclasses `FlowsClientConfigError` (missing configuration), `FlowsHTTPError` (non-2xx; carries `status_code` and response body), `FlowsNetworkError` (transport failure before a response), and `FlowsResponseError` (success status with malformed non-empty body). Success responses with an empty body return `None` (per clarification Q4); otherwise the parsed JSON is returned.
- **Rationale**: Spec FR-005–FR-008 require distinguishable failure modes under a single base type. Separating response-parse failures from HTTP failures keeps diagnostics precise.
- **Alternatives considered**: Reusing/raising `requests` exceptions directly (rejected: leaks the transport library into every integration's error handling, defeating the abstraction); two-level hierarchy folding parse errors into HTTP errors (rejected: a 200 with an unreadable body is not an HTTP failure and would confuse retry/handling logic in integrations).

## R6. Public API exposure

- **Decision**: Expose `FlowsClient` and all error types from `weni/flows/__init__.py`. Do **not** add a `Flows` re-export to the root `weni/__init__.py` in this task.
- **Rationale**: The subpackage `__init__.py` is the constitutional requirement; changing the root package surface is a user-visible API decision better made when the first real consumer lands, and keeping this task's diff minimal honors its tight scope (FR-011/FR-012).
- **Alternatives considered**: Root-level re-export `import weni.flows as Flows` (deferred: trivial follow-up, avoids speculative surface now).

## R7. Test strategy for 100% coverage

- **Decision**: Colocated suite in `weni/flows/tests/` using `pytest-mock` to patch `requests.request` (or the session call). Cover: each verb; URL normalization (trailing/leading slash combinations); header construction with bearer token; config precedence for each source level; default base URL fallback; missing-token and missing-required-value failures; non-2xx translation with status/body capture; network-failure translation; empty-body success; malformed-body error; request without payload. Coverage measured with the existing `--cov=weni` pytest configuration; the new module must report 100%.
- **Rationale**: Constitution Principle III mandates mocked external services and non-decreasing coverage; the user explicitly requires 100% for this feature. Enumerating the failure matrix up front makes the 100% target verifiable rather than aspirational.
- **Alternatives considered**: `responses`/`requests-mock` libraries (rejected: new dev dependencies; `pytest-mock` is already the established pattern in `weni/broadcasts/tests/test_sender.py`).
