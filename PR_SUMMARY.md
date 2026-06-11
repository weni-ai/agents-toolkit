# PR Summary: Flows Client Abstraction (`weni.flows`)

## What we did

- Created a new `weni/flows/` subpackage with a reusable, endpoint-agnostic HTTP client for the Flows platform:
  - `weni/flows/client.py` — `FlowsClient`, exposing `get`, `post`, `put`, `patch`, and `delete` convenience methods on top of a single private request executor. It handles URL normalization (no duplicate or missing slashes), header construction (`Content-Type: application/json` + `Authorization: Bearer <token>`), and response parsing (parsed JSON, or `None` for empty-body successes such as `204 No Content`).
  - `weni/flows/exceptions.py` — a typed error hierarchy under a single base: `FlowsClientError` with `FlowsClientConfigError` (missing configuration), `FlowsHTTPError` (non-2xx, exposing `status_code` and `response_body`), `FlowsNetworkError` (transport failures), and `FlowsResponseError` (unreadable success bodies). All errors chain the original exception for diagnostics.
- Implemented eager configuration resolution at construction time, with precedence `context.project` → `context.credentials` → `context.globals` → environment variable, falling back to the default Flows staging URL. A missing `auth_token` fails fast with `FlowsClientConfigError` — the client never sends unauthenticated requests.
- Added a fully mocked pytest suite (`weni/flows/tests/`) with 39 tests covering verb delegation, URL building, headers, payload forwarding, configuration precedence, fail-fast validation, and every error translation path — **100% coverage** of the new module, no real network calls.
- Release hygiene: bumped the version to `2.7.0` (MINOR), added a `CHANGELOG.md` entry, and added a "Flows Client" user-guide page to the docs site (`docs/user-guide/flows-client.md`, registered in `mkdocs.yml`).
- Scope guarantees honored: `weni/broadcasts/` was not modified in any way, and the client contains no knowledge of any specific Flows endpoint.

## Why we did it

- Today, every toolkit feature that talks to Flows has to hand-roll the same HTTP plumbing — resolving the base URL, validating and attaching the auth token, building well-formed URLs, and translating `requests` failures — as `weni/broadcasts/sender.py` does manually. This duplicates ~120 lines of boilerplate per integration and spreads subtle inconsistencies across the codebase.
- By centralizing that plumbing in `FlowsClient`, a new Flows integration only needs to write the endpoint path and the payload:

  ```python
  from weni.flows import FlowsClient

  client = FlowsClient(context)
  result = client.post('/api/v2/anything.json', json={'text': 'Hello'})
  ```

- The single `FlowsClientError` base type gives integrations one consistent way to handle every failure mode (configuration, HTTP, network, parsing) instead of each feature defining its own ad-hoc exceptions.
- Fail-fast configuration validation surfaces deployment misconfiguration at client construction with a clear, named error — before any request reaches Flows — instead of an opaque 401/403 at request time.
- This is deliberately an abstraction-only delivery: no existing feature was migrated and no endpoint integration was added, keeping the diff small and reviewable. Refactoring `weni/broadcasts/` to use the client is an intentional follow-up task.
