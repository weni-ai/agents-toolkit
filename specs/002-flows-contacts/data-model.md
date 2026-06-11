# Data Model: Flows Contacts Integration

**Feature**: 002-flows-contacts | **Date**: 2026-06-11

No persistent storage. Entities are in-memory values exchanged between the toolkit, `ContactSender`, `FlowsClient`, and the Flows contacts API.

## Contact (Flows response shape)

A contact record returned by Flows and passed through to the developer as `dict[str, Any]`.

| Field | Type | Notes |
|---|---|---|
| `uuid` | `str` | Contact UUID |
| `name` | `str \| null` | Display name |
| `language` | `str \| null` | ISO 639-3 code |
| `urns` | `list[str]` | Associated URNs |
| `groups` | `list[dict]` | `{name, uuid}` objects |
| `fields` | `dict[str, Any]` | Custom contact fields |
| `blocked` | `bool` | Blocked flag |
| `stopped` | `bool` | Opt-out flag |
| `created_on` | `str` | ISO datetime |
| `modified_on` | `str` | ISO datetime |
| `last_seen_on` | `str \| null` | ISO datetime |

The integration does **not** define a typed dataclass for contacts in v1; it forwards the Flows JSON object unchanged (same idiom as `BroadcastSender.send()` returning `response.json()`).

## ContactSender

Owns contacts-specific request building, URN logic, validation, and error translation. Uses `FlowsClient` for transport.

| Attribute | Type | Source | Notes |
|---|---|---|---|
| `context` | `Context` | constructor | Execution context |
| `client` | `FlowsClient` | constructed in `__init__` | Eager; raises `ContactSenderConfigError` if auth missing |
| `CONTACTS_PATH` | `str` (class const) | `'/api/v2/contacts.json'` | Single endpoint for get (GET) and update (POST) |

**Internal state per operation**:

| Value | Type | Notes |
|---|---|---|
| `effective_urn` | `str` | URN used for API calls; may differ from context URN after 9th-digit retry |
| `merged_body` | `dict[str, Any]` | Update payload after dict+kwargs merge |

## URN resolution

| Source | Precedence | Key path |
|---|---|---|
| Explicit argument | Highest (when provided) | `urn=` parameter |
| Contact URNs list | 1 | `context.contact['urns'][0]` |
| Contact URN field | 2 | `context.contact['urn']` |
| Parameters | 3 | `context.parameters['contact_urn']` |

**Validation**: If no URN resolves → `ContactSenderConfigError` before HTTP.

## 9th-digit alternate URN (WhatsApp Brazil)

Applied only when initial GET returns zero results **and** URN matches `whatsapp:55...`.

| Input path length | Condition | Alternate |
|---|---|---|
| 13 chars, digit at index 4 is `9` | Remove 9th digit | `path[:4] + path[5:]` |
| Otherwise | Insert 9 after area prefix | `path[:4] + '9' + path[4:]` |

On alternate match, `effective_urn = alternate_urn` for subsequent update POST.

## Update payload merge

```text
body = dict(payload or {})
body.update(kwargs)   # kwargs win on key conflict
```

| Rule | Error |
|---|---|
| Merged body empty | `ContactValidationError` |
| `'urns' in body` when updating by query URN | `ContactValidationError` |
| Any supported Flows write key present | Valid — forwarded as JSON body |

Supported write keys (non-exhaustive): `name`, `language`, `groups`, `fields`, and forward-compatible keys accepted by Flows.

## Flows list envelope (GET response)

Transient structure from Flows; not returned to caller.

| Field | Type | Notes |
|---|---|---|
| `results` | `list[dict]` | Contact objects |
| `next` | `str \| null` | Pagination cursor |
| `previous` | `str \| null` | Pagination cursor |

**Unwrap rules**:

| `len(results)` | Outcome |
|---|---|
| 0 | Retry 9th-digit if applicable; else `ContactNotFoundError` |
| 1 | Return `results[0]` |
| >1 | `ContactAmbiguousError` |

## Error hierarchy

```text
ContactSenderError (base — FR-009)
├── ContactSenderConfigError   # missing URN; FlowsClientConfigError mapped
├── ContactNotFoundError       # zero matches after retry
├── ContactAmbiguousError      # duplicate matches
└── ContactValidationError     # empty update body; urns in body
```

| Error | When | Carried data |
|---|---|---|
| `ContactSenderConfigError` | No resolvable URN; missing auth at client init | Message naming missing value |
| `ContactNotFoundError` | GET returns no contact for URN (after retry) | Message includes URN |
| `ContactAmbiguousError` | GET returns >1 contact | Message includes URN |
| `ContactValidationError` | Invalid update payload before HTTP | Message describes rule violated |
| `ContactSenderError` | Flows HTTP/network/response failures | Message includes Flows details; chain preserved |

## State transitions (update flow)

```text
resolve URN → GET by URN → [retry alternate?] → found?
  ├─ no  → ContactNotFoundError (no POST)
  └─ yes → merge/validate body → POST by effective_urn → return contact dict
```

No implicit create path exists in this integration.

## Contact facade

| Attribute | Type | Notes |
|---|---|---|
| `_tool` | `Tool` | Bound tool instance |
| Methods | `get(urn=None)`, `update(payload=None, urn=None, **kwargs)` | Delegate to `ContactSender` |

No event registration (unlike `Broadcast.register_broadcast`); contacts operations are read/write only.
