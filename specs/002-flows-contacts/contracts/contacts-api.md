# Public API Contract: `weni.contacts`

**Feature**: 002-flows-contacts | **Date**: 2026-06-11

Stable surface for toolkit developers. Internals may change freely.

## Imports

```python
from weni.contacts import (
	Contact,
	ContactSender,
	ContactSenderError,
	ContactSenderConfigError,
	ContactNotFoundError,
	ContactAmbiguousError,
	ContactValidationError,
)
```

## `Contact` (facade)

Tool-bound entry point mirroring `weni.broadcasts.Broadcast`.

### Construction

```python
contact_api = Contact(tool)
```

- `tool: weni.tool.Tool` — must expose `.context: Context`.

### `get`

```python
contact_api.get(urn=None)
```

| Parameter | Type | Description |
|---|---|---|
| `urn` | `str \| None` | Optional URN override. When omitted, resolved from context (see [data-model.md](../data-model.md)). |

**Returns**: `dict[str, Any]` — single Flows contact object.

**Raises**:

| Error | When |
|---|---|
| `ContactSenderConfigError` | No URN resolvable |
| `ContactNotFoundError` | No contact for URN (after 9th-digit retry when applicable) |
| `ContactAmbiguousError` | More than one contact matched |
| `ContactSenderError` | Flows HTTP/network/response failure |
| `ContactSenderConfigError` | Missing auth token (via FlowsClient at sender init) |

### `update`

```python
contact_api.update(payload=None, urn=None, **kwargs)
```

| Parameter | Type | Description |
|---|---|---|
| `payload` | `dict[str, Any] \| None` | Optional base write body |
| `urn` | `str \| None` | Optional URN override |
| `**kwargs` | write attributes | Merged into body; **override** conflicting keys from `payload` |

**Returns**: `dict[str, Any]` — updated contact object from Flows POST response.

**Guarantees**:

- Update-only: contact must exist (internal GET) before POST is sent; no implicit create.
- When GET succeeds via 9th-digit retry, POST uses the **matching** effective URN.
- Merged body must be non-empty.
- Merged body must not contain `urns` when identifying contact by query URN.

**Raises**: Same as `get`, plus `ContactValidationError` for invalid merged body.

## `ContactSender`

Lower-level API for use without the facade (testing or advanced callers).

### Construction

```python
sender = ContactSender(context)
```

Constructs internal `FlowsClient(context)`. **Raises** `ContactSenderConfigError` when auth token missing.

### Methods

Same signatures and behavior as the facade methods:

```python
sender.get(urn=None) -> dict[str, Any]
sender.update(payload=None, urn=None, **kwargs) -> dict[str, Any]
```

## Flows endpoint contract (external)

| Operation | HTTP | Path | Query | Body |
|---|---|---|---|---|
| Get by URN | GET | `/api/v2/contacts.json` | `urn=<encoded>` | — |
| Update by URN | POST | `/api/v2/contacts.json` | `urn=<effective_urn>` | merged write attributes |

Authorization and base URL are handled exclusively by `FlowsClient`.

## Error hierarchy contract

- All errors subclass `ContactSenderError`; `except ContactSenderError` is the broad catch.
- Domain errors (`ContactNotFoundError`, `ContactAmbiguousError`, `ContactValidationError`, `ContactSenderConfigError`) are part of the public contract for precise handling.
- Underlying `FlowsClientError` is translated at the sender boundary and not leaked raw.

## Compatibility

- Python >= 3.10; fully type-annotated; mypy-clean.
- Synchronous only.
- MINOR version bump + `CHANGELOG.md` entry when merged.
- Not re-exported from root `weni` package in this iteration.
