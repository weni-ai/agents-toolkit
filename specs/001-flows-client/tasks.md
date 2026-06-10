# Tasks: Flows Client Abstraction

**Input**: Design documents from `/specs/001-flows-client/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/client-api.md, quickstart.md

**Tests**: Included — the spec explicitly requires a fully mocked test suite (FR-010) and the user requires 100% coverage. Tests are written FIRST in each story phase and must FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This feature is a new domain subpackage of the published library: source in `weni/flows/`, tests colocated in `weni/flows/tests/` (per plan.md and Constitution Principle V). All formatting follows ruff config in `pyproject.toml` (line length 119, single quotes, tab indentation); everything fully type-annotated for mypy.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Turn the empty `weni/flows/` placeholder into a proper subpackage

- [ ] T001 Create package skeleton: `weni/flows/__init__.py` (module docstring only for now) and `weni/flows/tests/__init__.py` (empty); leave `weni/flows/resources/` untouched

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The error hierarchy every user story raises or catches

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Implement the error hierarchy in `weni/flows/exceptions.py`: `FlowsClientError` (base), `FlowsClientConfigError`, `FlowsHTTPError` (with public `status_code: int` and `response_body: str` attributes), `FlowsNetworkError`, `FlowsResponseError` — all with docstrings and full type annotations, per data-model.md "Error hierarchy"

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Make an authenticated request to Flows without manual plumbing (Priority: P1) 🎯 MVP

**Goal**: A toolkit developer issues authenticated requests to any Flows path via `client.get/post/put/patch/delete(path, ...)` with URL building, headers, auth, and response parsing handled by the client (FR-001, FR-002; contracts/client-api.md)

**Independent Test**: With `requests` mocked via pytest-mock, instantiate `FlowsClient` from a `Context` whose `project` mapping carries `flows_url` and `auth_token`, call each verb against an arbitrary path, and assert the correct URL, headers, body, and parsed response

### Tests for User Story 1 (write FIRST — must fail before T004)

- [ ] T003 [P] [US1] Write failing tests in `weni/flows/tests/test_client.py` mocking `requests.request` with pytest-mock: each verb (GET/POST/PUT/PATCH/DELETE) issues the right method; URL joining for all slash combinations (base with/without trailing slash × path with/without leading slash) never produces duplicate or missing slashes; headers always include `Content-Type: application/json` and `Authorization: Bearer <token>`; `json` payload and `params` are forwarded; requests without a body are supported; parsed JSON (dict and list) is returned; a 2xx response with an empty body returns `None`

### Implementation for User Story 1

- [ ] T004 [US1] Implement `FlowsClient` core in `weni/flows/client.py`: constructor taking `Context` and resolving `flows_url`/`auth_token` from `context.project` (resolution chain expanded in US2); base URL normalization; `_build_url`, `_build_headers`; private `_request(method, path, json, params)` executor using `requests` with no timeout; public `get`, `post`, `put`, `patch`, `delete` convenience methods; empty-body success → `None`; docstrings on all public members
- [ ] T005 [US1] Export the public API from `weni/flows/__init__.py`: `FlowsClient` plus all five error types from `weni/flows/exceptions.py`, with `__all__` and package docstring, matching contracts/client-api.md "Imports"

**Checkpoint**: `poetry run pytest weni/flows/tests/test_client.py` passes — core request abstraction fully functional and testable independently

---

## Phase 4: User Story 2 - Resolve configuration automatically from execution context (Priority: P2)

**Goal**: The client discovers base URL, auth token, and project UUID with precedence `context.project` → `context.credentials` → `context.globals` → environment variable → default, failing fast with a named configuration error when required values are missing (FR-003, FR-004, FR-005; data-model.md "Configuration resolution")

**Independent Test**: Construct `FlowsClient` from contexts and monkeypatched environments holding values at each precedence level and assert the resolved value; construct without an auth token and assert `FlowsClientConfigError` is raised before any request

### Tests for User Story 2 (write FIRST — must fail before T007)

- [ ] T006 [P] [US2] Write failing tests in `weni/flows/tests/test_config.py`: base URL precedence (`project` over `credentials` over `globals` over `FLOWS_BASE_URL` env var, using monkeypatch for env); fallback to default `https://flows.stg.cloud.weni.ai` when absent everywhere; resolved base URL is normalized (trailing slash stripped); `project_uuid` resolved from `uuid` key with `PROJECT_UUID` env fallback and `None` when absent; missing `auth_token` raises `FlowsClientConfigError` at construction with a message naming the key and its expected sources; no request is attempted when construction fails

### Implementation for User Story 2

- [ ] T007 [US2] Implement full configuration resolution in `weni/flows/client.py`: `_resolve_config(key, env_var, required)` helper with the precedence chain from research.md R3 (no `context.contact` lookup); `DEFAULT_FLOWS_URL` constant; eager resolution in `__init__` of `base_url`, `auth_token` (required, fail fast per clarification Q1), and `project_uuid` (optional); `FlowsClientConfigError` messages naming the missing key and sources

**Checkpoint**: User Stories 1 AND 2 work independently — `poetry run pytest weni/flows/tests/` passes

---

## Phase 5: User Story 3 - Receive consistent, typed errors for failed requests (Priority: P3)

**Goal**: All failures surface as the client's own error types — non-2xx → `FlowsHTTPError` with status and body, transport failure → `FlowsNetworkError`, unreadable success body → `FlowsResponseError` — all catchable via `FlowsClientError` (FR-006, FR-007, FR-008)

**Independent Test**: With `requests` mocked to return non-2xx responses, raise transport exceptions, and return malformed bodies, assert each failure maps to the right error type carrying the right data, and that `except FlowsClientError` catches every mode

### Tests for User Story 3 (write FIRST — must fail before T009)

- [ ] T008 [P] [US3] Write failing tests in `weni/flows/tests/test_exceptions.py`: non-2xx response raises `FlowsHTTPError` exposing `status_code` and `response_body`; transport failure (`requests.exceptions.RequestException`) raises `FlowsNetworkError` with the original exception chained (`__cause__`); 2xx with a malformed non-empty body raises `FlowsResponseError` indicating the body was unreadable; `FlowsClientConfigError`, `FlowsHTTPError`, `FlowsNetworkError`, and `FlowsResponseError` are all subclasses of `FlowsClientError` (single-catch guarantee)

### Implementation for User Story 3

- [ ] T009 [US3] Implement error translation in `weni/flows/client.py` `_request`: `response.raise_for_status()` → catch `requests.exceptions.HTTPError` and raise `FlowsHTTPError(status_code, response_body)`; catch `requests.exceptions.RequestException` and raise `FlowsNetworkError`; catch JSON decode failure on non-empty 2xx bodies and raise `FlowsResponseError`; always chain with `raise ... from` so transport diagnostics are preserved

**Checkpoint**: All user stories independently functional — full failure matrix covered

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Library release hygiene (Constitution: Development Workflow) and final scope/quality verification

- [ ] T010 [P] Add a `## 2.7.0` entry to `CHANGELOG.md` describing the new `weni.flows` client (new feature: Flows API client abstraction with typed error hierarchy)
- [ ] T011 [P] Bump version from `2.6.4` to `2.7.0` (MINOR — backwards-compatible addition) in `pyproject.toml`
- [ ] T012 [P] Add a user-guide page for the Flows client in `docs/user-guide/flows-client.md` documenting construction, configuration sources, request methods, and error handling per contracts/client-api.md, and register it in the `nav` section of `mkdocs.yml`
- [ ] T013 Run the quality gates from quickstart.md: `poetry run ruff check .` (zero violations), `poetry run mypy weni` (zero errors), `poetry run pytest` (all pass); verify `weni/flows/client.py` and `weni/flows/exceptions.py` report **100%** coverage and overall `weni` coverage has not decreased; fix anything that fails
- [ ] T014 Verify scope guards from quickstart.md: `git diff main --stat -- weni/broadcasts/` outputs nothing (FR-011/SC-003) and `weni/flows/` source contains no endpoint-specific paths such as `whatsapp_broadcasts` (FR-012)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Phase 2; sequential by priority is recommended because all three stories touch `weni/flows/client.py` (see below)
- **Polish (Phase 6)**: T010–T012 can start anytime after Phase 3; T013/T014 require all stories complete

### User Story Dependencies

- **US1 (P1)**: Only Phase 2 — delivers the MVP alone
- **US2 (P2)**: Independently testable, but its implementation task (T007) edits `weni/flows/client.py`, so it should follow T004 to avoid same-file conflicts
- **US3 (P3)**: Independently testable, but T009 also edits `weni/flows/client.py` `_request`, so it should follow T004 (and T007 if US2 is done first)

### Within Each User Story

- Test task MUST be written and FAIL before the implementation task
- T004 before T005 (exports reference the implemented class)

### Parallel Opportunities

- T003, T006, T008 (test files) are all different files — they can be written in parallel as soon as Phase 2 completes
- T010, T011, T012 (changelog, version bump, docs) are different files — fully parallel
- Implementation tasks T004, T007, T009 are NOT parallel (same file: `weni/flows/client.py`)

---

## Parallel Example: After Phase 2

```bash
# Write all three failing test suites in parallel (different files):
Task: "T003 — tests for request execution in weni/flows/tests/test_client.py"
Task: "T006 — tests for config resolution in weni/flows/tests/test_config.py"
Task: "T008 — tests for error translation in weni/flows/tests/test_exceptions.py"

# Polish tasks in parallel (different files):
Task: "T010 — CHANGELOG.md entry"
Task: "T011 — version bump in pyproject.toml"
Task: "T012 — docs/user-guide/flows-client.md + mkdocs.yml nav"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002 — CRITICAL, blocks all stories)
3. Complete Phase 3: T003 (failing tests) → T004 → T005
4. **STOP and VALIDATE**: `poetry run pytest weni/flows/tests/test_client.py` — the request abstraction works end-to-end with mocked transport
5. Demo-able MVP: authenticated requests to arbitrary Flows paths with zero manual plumbing

### Incremental Delivery

1. Setup + Foundational → package skeleton + error types ready
2. US1 → core request abstraction (MVP!)
3. US2 → full configuration resolution with fail-fast validation
4. US3 → complete typed error translation
5. Polish → changelog, version, docs, gates, scope guards → ready for PR

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- Verify each test task fails before implementing its counterpart
- Commit after each task or logical group (convention: `feat:`, `tests:`, `build:`)
- The spec forbids touching `weni/broadcasts/` and integrating any specific Flows endpoint — T014 enforces both
- Total: 14 tasks (1 setup, 1 foundational, 3 for US1, 2 for US2, 2 for US3, 5 polish); 100% coverage is a hard gate (T013)
