# Tasks: Flows Contacts Integration

**Input**: Design documents from `/specs/002-flows-contacts/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/contacts-api.md, quickstart.md

**Tests**: Included — the spec requires a fully mocked test suite (FR-010) and the plan/user require **100% coverage** for `weni/contacts/`. Tests are written FIRST in each story phase and must FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This feature is a new domain subpackage of the published library: source in `weni/contacts/`, tests colocated in `weni/contacts/tests/` (per plan.md and Constitution Principle V). Formatting follows ruff config in `pyproject.toml` (line length 119, single quotes, tab indentation); everything fully type-annotated for mypy. Transport MUST go through `FlowsClient` only — no direct `requests` usage in `weni/contacts/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new `weni/contacts/` subpackage skeleton mirroring `weni/broadcasts/`

- [X] T001 Create package skeleton: `weni/contacts/__init__.py` (module docstring only for now), `weni/contacts/contact.py` (module docstring stub), `weni/contacts/sender.py` (module docstring stub), `weni/contacts/tests/__init__.py` (empty), and `weni/contacts/tests/conftest.py` with a shared `create_context()` helper (reused by `test_sender.py` and `test_contact.py`) mirroring `weni/broadcasts/tests/test_sender.py` (project/credentials/globals/contact/parameters kwargs, `_default_project()` with `flows_url` and `auth_token`); run `ruff format` on new files (tab indentation per plan, not broadcasts' space style)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Error hierarchy and sender shell that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Implement the error hierarchy at the top of `weni/contacts/sender.py`: `ContactSenderError` (base), `ContactSenderConfigError`, `ContactNotFoundError`, `ContactAmbiguousError`, `ContactValidationError` — all with docstrings and full type annotations, per data-model.md "Error hierarchy" and contracts/contacts-api.md
- [X] T003 Implement `ContactSender.__init__` in `weni/contacts/sender.py`: store `context`, construct `FlowsClient(context)` eagerly, map `FlowsClientConfigError` to `ContactSenderConfigError`; define `CONTACTS_PATH = '/api/v2/contacts.json'` constant

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Retrieve the current conversation contact from Flows (Priority: P1) 🎯 MVP

**Goal**: A toolkit developer calls `ContactSender.get(urn=None)` and receives a single Flows contact dict resolved from the conversation URN, with list-envelope unwrapping, not-found/ambiguous errors, and WhatsApp Brazil 9th-digit retry (FR-004, FR-005, FR-005a, FR-008)

**Independent Test**: With `FlowsClient.get` mocked, provide a `Context` with a contact URN, call `get()`, assert GET to `/api/v2/contacts.json?urn=...`, unwrapped contact dict returned; assert not-found, ambiguous, missing-URN, and retry scenarios per acceptance scenarios in spec.md User Story 1

### Tests for User Story 1 (write FIRST — must fail before T005)

- [X] T004 [US1] Write failing tests in `weni/contacts/tests/test_sender.py` mocking `FlowsClient.get`: URN resolution precedence (`contact.urns[0]` → `contact.urn` → `parameters.contact_urn`), explicit `urn` override, missing URN raises `ContactSenderConfigError` before HTTP; successful get unwraps `results[0]` from list envelope; zero results raises `ContactNotFoundError`; multiple results raises `ContactAmbiguousError`; WhatsApp Brazil `whatsapp:55...` retry tries alternate 9th-digit URN before final not-found; non-`whatsapp:55` URNs skip retry; GET passes URN via `params={'urn': ...}` with correct value for URNs requiring encoding (e.g. `whatsapp:5582999893640`); `FlowsHTTPError`/`FlowsNetworkError`/`FlowsResponseError` from client mapped to `ContactSenderError`; `FlowsClientConfigError` at init maps to `ContactSenderConfigError`

### Implementation for User Story 1

- [X] T005 [US1] Implement URN helpers in `weni/contacts/sender.py`: `_get_contact_urn()`, `_resolve_urn(urn: str | None) -> str` (explicit override or context resolution, raise `ContactSenderConfigError` when missing), mirroring `BroadcastSender._get_contact_urn()` precedence from research.md R4
- [X] T006 [US1] Implement lookup helpers in `weni/contacts/sender.py`: `_alternate_whatsapp_brazil_urn(urn: str) -> str | None` (9th-digit toggle per research.md R5 / Flows `ContactsEndpoint.get_object` logic), `_fetch_list(urn: str) -> list[dict]`, `_get_by_urn(urn: str) -> tuple[dict[str, Any], str]` returning `(contact_dict, effective_urn)` with retry, not-found, and ambiguous handling
- [X] T007 [US1] Implement public `ContactSender.get(self, urn: str | None = None) -> dict[str, Any]` in `weni/contacts/sender.py`: delegate to `_get_by_urn`, return contact dict; wrap `FlowsClientError` subclasses (except config, already at init) into `ContactSenderError` with chained cause; docstring per contracts/contacts-api.md

**Checkpoint**: `poetry run pytest weni/contacts/tests/test_sender.py -k get` passes — get-by-URN fully functional and independently testable

---

## Phase 4: User Story 2 - Update contact attributes on the conversation contact (Priority: P2)

**Goal**: A toolkit developer calls `ContactSender.update(payload=None, urn=None, **kwargs)` to update an **existing** contact with the **full Flows write surface** (`fields`, `name`, `language`, `groups`, etc.), hybrid payload merge, validation, and update-only semantics (FR-006, FR-006a, FR-007, FR-008)

**Independent Test**: With `FlowsClient.get` and `FlowsClient.post` mocked, call `update(fields={...})` or `update(name='...')`, assert GET existence check precedes POST, POST uses effective URN after 9th-digit retry, merged body correct, empty/`urns`-in-body rejected, not-found skips POST, URN passed via encoded query params

### Tests for User Story 2 (write FIRST — must fail before T009)

- [X] T008 [P] [US2] Write failing tests in `weni/contacts/tests/test_sender.py` (extend existing file) mocking `FlowsClient.get` and `FlowsClient.post`: successful update sends POST with correct `urn` query param (including URL-safe encoding for URNs like `whatsapp:5582999893640`) and merged JSON body; dict-only (`fields`), kwargs-only (`name=...`), and hybrid payloads with kwargs overriding dict keys on conflict; at least one top-level write attribute (e.g. `name`) sent in POST body per full write surface; empty merged body raises `ContactValidationError` before HTTP; `urns` in merged body raises `ContactValidationError`; not-found on existence GET raises `ContactNotFoundError` and `post` is never called; after 9th-digit retry on GET, POST uses the effective matching URN; explicit `urn` override on update; `FlowsHTTPError` and `FlowsNetworkError` on POST mapped to `ContactSenderError`; returns updated contact dict from POST response

### Implementation for User Story 2

- [X] T009 [US2] Implement payload helpers in `weni/contacts/sender.py`: `_merge_update_payload(payload: dict[str, Any] | None, kwargs: dict[str, Any]) -> dict[str, Any]` (kwargs win on conflict), `_validate_update_body(body: dict[str, Any]) -> None` (reject empty body and `urns` key with `ContactValidationError`)
- [X] T010 [US2] Implement public `ContactSender.update(self, payload: dict[str, Any] | None = None, urn: str | None = None, **kwargs) -> dict[str, Any]` in `weni/contacts/sender.py`: resolve URN, run existence check via `_get_by_urn` (update-only — no POST if not found), merge/validate body, `FlowsClient.post(CONTACTS_PATH, params={'urn': effective_urn}, json=body)`, return POST response dict; docstring per contracts/contacts-api.md

**Checkpoint**: User Stories 1 AND 2 work independently — get and update both pass in `weni/contacts/tests/test_sender.py`

---

## Phase 5: User Story 3 - Use the integration from tool execution with the same ergonomics as broadcasts (Priority: P3)

**Goal**: Toolkit developers use `Contact(tool).get()` / `Contact(tool).update(...)` with public exports matching broadcasts ergonomics (FR-001, User Story 3)

**Independent Test**: Construct a mock `Tool` with `.context`, call `Contact(tool).get()` and `.update(...)`, verify lazy `ContactSender` delegation without manual client setup

### Tests for User Story 3 (write FIRST — must fail before T012)

- [X] T011 [P] [US3] Write failing tests in `weni/contacts/tests/test_contact.py`: `Contact(tool).get()` delegates to `ContactSender.get()` with tool context; `Contact(tool).update(...)` delegates to `ContactSender.update(...)` forwarding payload/urn/kwargs; when sender raises `ContactNotFoundError` (or other contacts-specific errors), facade propagates the same error unchanged (spec User Story 3 acceptance scenario 2); uses lazy import of `ContactSender` (patch at `weni.contacts.contact.ContactSender` or equivalent)

### Implementation for User Story 3

- [X] T012 [US3] Implement `Contact` facade in `weni/contacts/contact.py`: `__init__(self, tool: Tool)` storing `_tool`, `_get_sender() -> ContactSender` lazy import mirroring `weni/broadcasts/broadcast.py`, public `get(urn=None)` and `update(payload=None, urn=None, **kwargs)` delegating to sender; docstring with usage example per contracts/contacts-api.md
- [X] T013 [US3] Export public API from `weni/contacts/__init__.py`: `Contact`, `ContactSender`, and all five error types with `__all__` and package docstring, matching contracts/contacts-api.md "Imports"

**Checkpoint**: All three user stories independently functional — facade + sender + exports complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Release hygiene, 100% module coverage verification, and scope guards

- [X] T014 [P] Add a `## 2.8.0` entry to `CHANGELOG.md` describing the new `weni.contacts` integration (get/update contact by URN via FlowsClient, update-only semantics, 9th-digit retry, hybrid update payloads)
- [X] T015 [P] Bump version from `2.7.1` to `2.8.0` (MINOR — backwards-compatible addition) in `pyproject.toml`
- [X] T016 [P] Add a user-guide page at `docs/user-guide/contacts.md` documenting `Contact`/`ContactSender` usage, URN resolution, get/update semantics, error types, and full write surface per `contracts/contacts-api.md`; register it in the `nav` section of `mkdocs.yml` (constitution Development Workflow — public API docs)
- [X] T017 Run quality gates from `specs/002-flows-contacts/quickstart.md`: `poetry run ruff check .` (zero violations), `poetry run mypy weni` (zero errors), `poetry run pytest weni/contacts/tests/ --cov=weni.contacts --cov-report=term-missing` (**100%** coverage for all `weni/contacts/` modules); then `poetry run pytest` (all pass, overall `weni` coverage >= 95%); fix anything that fails
- [X] T018 Verify scope guards from quickstart.md: `git diff main --stat -- weni/broadcasts/` outputs nothing (FR-011); `rg -n "requests\\.(get|post|request)" weni/contacts/` matches nothing outside tests if at all (FR-002 — FlowsClient only)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Phase 2; US2 depends on US1 (`update` calls `_get_by_urn` from US1); US3 depends on US1+US2 (facade delegates both methods)
- **Polish (Phase 6)**: T014–T016 can start after T013; T017–T018 require all stories complete (T017 after T016 so docs exist before final gate run)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependency on other stories; **MVP scope**
- **User Story 2 (P2)**: Depends on US1 — reuses `_get_by_urn` for existence check and effective URN; independently testable via mocked GET+POST
- **User Story 3 (P3)**: Depends on US1+US2 — thin facade over completed sender; independently testable via mocked sender

### Within Each User Story

- Tests MUST be written and FAIL before implementation tasks in that story
- Sender helpers before public methods
- Story complete before moving to next priority

### Parallel Opportunities

- T004 runs immediately after Phase 2 (before T005–T007 implementation); not parallel with other US1 impl tasks
- T008 parallel-ready once US1 implementation (T005–T007) complete
- T011 parallel-ready once US2 complete (different file: `test_contact.py` vs `test_sender.py`)
- T014, T015, and T016 parallelizable in Polish phase

---

## Parallel Example: User Story 1

```bash
# After Phase 2, write tests first:
Task T004: "Write failing tests in weni/contacts/tests/test_sender.py ..."

# Then implement sequentially (same file weni/contacts/sender.py):
Task T005 → T006 → T007
```

---

## Parallel Example: User Story 3

```bash
# Tests in separate file can start once sender API is stable:
Task T011: "Write failing tests in weni/contacts/tests/test_contact.py ..."

# Facade + exports (T012–T013) after tests fail
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T003)
3. Complete Phase 3: User Story 1 (T004–T007)
4. **STOP and VALIDATE**: `poetry run pytest weni/contacts/tests/test_sender.py -k get --cov=weni.contacts --cov-report=term-missing`
5. Demo: retrieve conversation contact by URN inside a tool

### Incremental Delivery

1. Setup + Foundational → sender shell ready
2. User Story 1 → get-by-URN works → **MVP**
3. User Story 2 → update with validation and update-only semantics
4. User Story 3 → `Contact(tool)` facade + public exports
5. Polish → CHANGELOG, version bump, user-guide docs, 100% coverage gate, scope guards

### Parallel Team Strategy

With multiple developers after Phase 2:

- Developer A: US1 (T004–T007) — blocks B's update work
- Developer B: US2 (T008–T010) — starts after US1 `_get_by_urn` lands
- Developer C: US3 (T011–T013) — starts after US2 `update` lands

---

## Notes

- All tasks use strict checklist format: `- [X] T### [P?] [US?] Description with file path`
- Do not modify `weni/broadcasts/` (FR-011)
- Do not use direct `requests` in `weni/contacts/` source — only `FlowsClient` (FR-002)
- Target **100%** line coverage for `weni/contacts/` (plan + constitution floor 95% overall)
- Commit after each task or logical group; stop at any checkpoint to validate independently
