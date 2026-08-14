# Contacts

The Contacts module lets tools read and update Flows contact records for the current conversation during execution. All HTTP traffic goes through `FlowsClient` — you never hand-roll requests to `/api/v2/contacts.json`.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context):
        contact = self.contact.get()
        self.contact.update(fields={"email": "user@example.com"})
        return FinalResponse()
```

`self.contact` is a `Contact` instance pre-bound to the tool. It is created on first access and cached for the duration of the execution.

## Calling Styles

All three styles are equivalent. Choose whichever fits your convention:

```python
# Namespaced (recommended) — available via self.<name> on any Tool
contact = self.contact.get()
self.contact.update(fields={"email": "user@example.com"})

# Shorthand — mirrors the old API, resolved through the same facade
contact = self.get_contact()
self.update_contact({"fields": {"email": "user@example.com"}})

# Explicit — pass the tool instance yourself
from weni.contacts import Contact
contact = Contact(self).get()
Contact(self).update(fields={"email": "user@example.com"})
```

## How It Works

```
   Tool.execute()                        Flows API
   ──────────────                        ─────────
   self.contact.get()
        │
        ▼
   ContactSender
   GET /api/v2/contacts.json?urn=... ──────► Returns contact list envelope
        │                                    (single result unwrapped)
        ▼
   self.contact.update(fields={...})
        │
        ├── GET existence check (same URN resolution + 9th-digit retry)
        │
        ▼
   POST /api/v2/contacts.json?urn=... ─────► Returns updated contact
        json={ merged write attributes }
```

1. `get()` resolves the contact URN from context (or an explicit override), fetches the contact, and returns a single contact dict.
2. `update()` validates the write body, confirms the contact exists, then POSTs the merged attributes using the **effective** URN (after 9th-digit retry when applicable).
3. Updates are **update-only** — if no contact matches the URN, the integration raises `ContactNotFoundError` and never sends a POST.

## URN Resolution

When you omit `urn`, the sender resolves it from the execution context with this precedence:

| Priority | Source |
|---|---|
| 1 | `contact.urns[0]` |
| 2 | `contact.urn` |
| 3 | `parameters.contact_urn` |

Pass `urn=` to override context resolution for either `get()` or `update()`:

```python
contact = self.contact.get(urn="whatsapp:5511999990000")
self.contact.update(name="Maria", urn="whatsapp:5511999990000")
```

### WhatsApp Brazil 9th-digit retry

For URNs starting with `whatsapp:55`, lookup retries with the alternate 9th-digit variant when the first GET returns no match — mirroring Flows `ContactsEndpoint` behavior. If the retry finds exactly one contact, that URN is used for subsequent operations (including the POST on update).

## Update Payloads

`update()` accepts a hybrid API: an optional dict plus keyword arguments. Keyword arguments **override** conflicting keys from the dict.

```python
# Dict only
self.contact.update({"fields": {"email": "a@example.com"}})

# Kwargs only (recommended)
self.contact.update(name="Leonardo")
self.contact.update(fields={"email": "a@example.com"})

# Hybrid — name kwarg wins on conflict
self.contact.update({"name": "Old", "language": "por"}, name="Leonardo")
```

Supported write attributes follow the Flows contacts POST surface: `fields`, `name`, `language`, `groups`, and other top-level attributes accepted by Flows.

Validation rules:

- The merged body must not be empty.
- The merged body must not include `urns` when the contact is identified by the query URN.

## Operation Log

Each `get()` and `update()` call is recorded in the tool's operation log and included in the response:

```python
{
    "result": <data>,
    "contacts_get":     [<urn>, …],       # one entry per get()
    "contacts_updated": [<merged body>, …] # one entry per update()
}
```

These keys only appear in the result when at least one operation was performed.

Entries are recorded **after** the Flows call succeeds. An update rejected by Flows (or a `get()` that finds no contact) raises and leaves the log untouched, so the platform never sees an operation that did not happen.

## Context Refresh

After a successful `update()`, the contact returned by Flows is merged back into `context.contact`, so the rest of the execution reads the current state:

```python
def execute(self, context: Context):
    self.contact.update(fields={"email": "user@example.com"})
    context.contact["fields"]["email"]  # "user@example.com"
```

Only contact attributes are merged — `fields`, `name`, `language`, `groups`, and `urns`. Platform metadata from the response (`uuid`, `created_on`, `modified_on`, `blocked`, `stopped`) is ignored so the namespace does not drift from what the platform provides.

`fields` is merged key by key, keeping values you did not update. Every other attribute is replaced with the value Flows returned. The refresh reads the response, not the payload you sent, because Flows normalizes values on write.

The refresh applies to the current invocation only. Persisting the change across conversation turns depends on the platform applying the `contacts_updated` log to the session memory.

## Configuration

Configuration is resolved by `FlowsClient` when `ContactSender` is constructed:

| Value | Context keys (priority order) | Environment fallback | Required |
|---|---|---|---|
| Base URL | `flows_url` in `project` → `credentials` → `globals` | `FLOWS_BASE_URL` | No (defaults to staging) |
| Auth token | `auth_token` in `project` | — | Yes |

Missing auth token raises `ContactSenderConfigError` at construction.

## Error Handling

All contacts failures subclass `ContactSenderError`:

```python
from weni.contacts import (
    ContactSenderError,
    ContactSenderConfigError,
    ContactNotFoundError,
    ContactAmbiguousError,
    ContactValidationError,
)

try:
    self.contact.update(name="Leonardo")
except ContactNotFoundError:
    ...
except ContactValidationError:
    ...
except ContactSenderError:
    ...
```

| Error | Raised when |
|---|---|
| `ContactSenderConfigError` | Missing auth token or contact URN |
| `ContactNotFoundError` | No contact for URN (after 9th-digit retry when applicable) |
| `ContactAmbiguousError` | More than one contact matched |
| `ContactValidationError` | Empty update body or `urns` in body |
| `ContactSenderError` | Flows HTTP, network, or response parsing failure |

Underlying `FlowsClientError` types are translated at the sender boundary and not leaked raw.

## Lower-Level API

Use `ContactSender` directly when you have a `Context` but not a `Tool`:

```python
from weni.contacts import ContactSender

sender = ContactSender(context)
contact = sender.get()
updated = sender.update(fields={"email": "user@example.com"})
```

Method signatures and behavior match the `Contact` facade.

## Test Definition

For testing via `weni run`, pass config through `project` and `contact`:

```yaml
tests:
    test_get_contact:
        project:
            auth_token: "your-jwt-token"
            flows_url: "https://flows.weni.ai"
        contact:
            urn: "whatsapp:5511999990000"

    test_update_contact:
        parameters:
            email: "user@example.com"
        project:
            auth_token: "your-jwt-token"
            flows_url: "https://flows.weni.ai"
        contact:
            urn: "whatsapp:5511999990000"
```
