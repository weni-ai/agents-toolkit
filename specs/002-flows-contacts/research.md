# Research: Flows Contacts Integration

**Feature**: 002-flows-contacts | **Date**: 2026-06-11

All Technical Context items are resolved; decisions below consolidate design choices grounded in the spec clarifications, `weni/broadcasts/`, `weni/flows/`, and the Flows contacts endpoint behavior.

## R1. Package layout (broadcasts mirror)

- **Decision**: New subpackage `weni/contacts/` with `contact.py` (facade), `sender.py` (HTTP semantics), `__init__.py` (exports), and `tests/` colocated.
- **Rationale**: Spec FR-001 and user planning input require broadcasts-like structure. Facade binds to `Tool` and lazy-imports sender, matching `Broadcast` → `BroadcastSender`.
- **Alternatives considered**: Single-module implementation (rejected: violates Principle V and broadcasts precedent); putting contacts logic inside `weni/flows/resources/` (rejected: endpoint-specific logic belongs in its own domain package).

## R2. Transport layer — FlowsClient only

- **Decision**: `ContactSender` constructs a `FlowsClient(context)` and calls `client.get(...)` / `client.post(...)` exclusively. No direct `requests` usage, no duplicated URL/header/auth resolution.
- **Rationale**: Spec FR-002/SC-004; this is the first consumer of the flows client abstraction for a real endpoint.
- **Alternatives considered**: Copy `BroadcastSender` raw requests pattern (rejected: spec explicitly mandates shared client); subclass `FlowsClient` (rejected: unnecessary — composition in sender is sufficient).

## R3. Contacts endpoint mapping

- **Decision**:
  - Path constant: `CONTACTS_PATH = '/api/v2/contacts.json'`
  - **Get by URN**: `FlowsClient.get(CONTACTS_PATH, params={'urn': urn})` → unwrap `results[0]` when exactly one result; raise typed errors for 0 or >1 results (after retry).
  - **Update by URN**: existence check via internal get, then `FlowsClient.post(CONTACTS_PATH, params={'urn': effective_urn}, json=merged_body)`.
- **Rationale**: Matches Flows `ContactsEndpoint` documented behavior and user curl example. Query param encoding handled by `requests` via `params`.
- **Alternatives considered**: UUID-based lookup (deferred per spec assumptions); DELETE/list endpoints (out of scope).

## R4. URN resolution (shared with broadcasts)

- **Decision**: `_get_contact_urn()` with precedence `contact.urns[0]` → `contact.urn` → `parameters.contact_urn`. Optional explicit `urn` argument on public methods overrides context resolution. Missing URN raises `ContactSenderConfigError` before any request.
- **Rationale**: Spec FR-003; identical to `BroadcastSender._get_contact_urn()` for cross-feature predictability.
- **Alternatives considered**: Including `context.credentials` in URN lookup (rejected: not used by broadcasts; URN is conversation identity not deployment config).

## R5. WhatsApp Brazil 9th-digit retry

- **Decision**: When get-by-URN returns zero results and URN scheme is `whatsapp` with path starting `55`, compute alternate URN using the same digit-toggle logic as Flows `ContactsEndpoint.get_object` (13-digit with 9 at index 4 → remove; otherwise insert 9 after country+area prefix). Retry get once; on success, **effective URN** for update is the URN that matched.
- **Rationale**: Clarification Q3; reduces false not-found for Brazilian WhatsApp numbers without requiring org config in context.
- **Alternatives considered**: Server-only retry (rejected: GET filter in Flows does not apply POST's `verify_ninth_digit` path for all orgs); always retry for any whatsapp URN (rejected: spec scopes to `whatsapp:55...`).

## R6. Update-only semantics

- **Decision**: `update()` always calls internal get/existence check first. If not found (after retry), raise `ContactNotFoundError` and **never** POST. If found, POST with effective URN.
- **Rationale**: Clarification Q2 overrides Flows default create-on-POST behavior.
- **Alternatives considered**: Rely on Flows 201 detection after POST (rejected: would create contacts); separate `create()` method (out of scope).

## R7. Update payload — hybrid dict + kwargs

- **Decision**: Signature `update(self, payload: dict[str, Any] | None = None, *, urn: str | None = None, **kwargs) -> dict[str, Any]`. Merge: start from `payload or {}`, then `body.update(kwargs)` so kwargs win on conflict. Reject empty merged body with `ContactValidationError`. Reject merged body containing `urns` key with `ContactValidationError` (clarification Q4).
- **Rationale**: Clarification Q5 + full write surface (Q1).
- **Alternatives considered**: Typed dataclass for write payload (rejected: conflicts with full write surface and Flows forward-compatibility); kwargs-only (rejected by Q5).

## R8. Error hierarchy

- **Decision**:

  ```text
  ContactSenderError (base)
  ├── ContactSenderConfigError   # missing URN / FlowsClientConfigError wrapper
  ├── ContactNotFoundError       # zero results after retry
  ├── ContactAmbiguousError      # >1 result for URN filter
  └── ContactValidationError     # empty payload, urns in body
  ```

  Map `FlowsClientError` subclasses at sender boundary:
  - `FlowsClientConfigError` → `ContactSenderConfigError`
  - `FlowsHTTPError` → `ContactSenderError` with status/body in message (no separate HTTP subclass — matches broadcasts pattern)
  - `FlowsNetworkError` / `FlowsResponseError` → `ContactSenderError`

- **Rationale**: Spec FR-009/SC-005; mirrors broadcasts two-level hierarchy extended with domain-specific not-found/validation/ambiguous types.
- **Alternatives considered**: Re-raise raw `FlowsClientError` (rejected: spec requires contacts-specific types); single error class only (rejected: SC-005 requires distinguishable modes).

## R9. Public API exposure

- **Decision**: Export `Contact`, `ContactSender`, and all error types from `weni/contacts/__init__.py`. Update `CHANGELOG.md` on merge. Do not re-export from root `weni/__init__.py`.
- **Rationale**: Matches flows client deferral (R6 in 001-flows-client); import path `from weni.contacts import Contact`.
- **Alternatives considered**: Root re-export (deferred).

## R10. Test strategy — 100% module coverage

- **Decision**: Colocated suite in `weni/contacts/tests/` patching `FlowsClient.get` / `FlowsClient.post` (or patch at module import site). Minimum matrix:

  | Area | Cases |
  |---|---|
  | URN resolution | urns list, urn field, parameters fallback, precedence, explicit override, missing URN |
  | Get success | single result unwrap, returns contact dict not envelope |
  | Get failures | empty results → not found; multiple results → ambiguous |
  | 9th-digit retry | no match then alternate matches; both fail; non-Brazil skip retry |
  | Update success | dict-only, kwargs-only, hybrid merge precedence, uses effective URN after retry |
  | Update guardrails | empty payload; urns in merged body; not-found skips POST |
  | Error mapping | FlowsHTTPError, FlowsNetworkError, FlowsClientConfigError → contacts errors |
  | Facade | `Contact(tool).get()` / `.update()` delegate to sender |

  Run: `poetry run pytest weni/contacts/tests/ --cov=weni.contacts --cov-report=term-missing` → **100%** for `weni/contacts/`.

- **Rationale**: User planning input + constitution Principle III; enumerated matrix makes 100% verifiable.
- **Alternatives considered**: Integration tests against real Flows (rejected: constitution forbids real network); shared conftest with flows tests only (rejected: broadcasts pattern uses local `create_context` helper).
