# Contacts

The Contacts module lets tools read and update Flows contact records for the current conversation during execution. All HTTP traffic goes through `FlowsClient` — you never hand-roll requests to `/api/v2/contacts.json`.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.contacts import Contact
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context):
        contact = Contact(self).get()
        Contact(self).update(fields={'email': 'leonardo.amaral@vtex.com'})
        return FinalResponse()
```

`Contact(self)` receives the tool instance, which provides the execution context (including the conversation contact URN).

## How It Works

```
   Tool.execute()                        Flows API
   ──────────────                        ─────────
   Contact(self).get()
        │
        ▼
   ContactSender
   GET /api/v2/contacts.json?urn=... ──────► Returns contact list envelope
        │                                    (single result unwrapped)
        ▼
   Contact(self).update(fields={...})
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

Pass `urn=` to override context resolution for either `get()` or `update()`.

### WhatsApp Brazil 9th-digit retry

For URNs starting with `whatsapp:55`, lookup retries with the alternate 9th-digit variant when the first GET returns no match — mirroring Flows `ContactsEndpoint` behavior. If the retry finds exactly one contact, that URN is used for subsequent operations (including the POST on update).

## Update Payloads

`update()` accepts a hybrid API: an optional dict plus keyword arguments. Keyword arguments **override** conflicting keys from the dict.

```python
# Dict only
Contact(self).update(fields={'email': 'a@example.com'})

# Kwargs only
Contact(self).update(name='Leonardo')

# Hybrid — name wins on conflict
Contact(self).update({'name': 'Old', 'language': 'por'}, name='Leonardo')
```

Supported write attributes follow the Flows contacts POST surface: `fields`, `name`, `language`, `groups`, and other top-level attributes accepted by Flows.

Validation rules:

- The merged body must not be empty.
- The merged body must not include `urns` when the contact is identified by the query URN.

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
    Contact,
    ContactSenderError,
    ContactSenderConfigError,
    ContactNotFoundError,
    ContactAmbiguousError,
    ContactValidationError,
)

try:
    Contact(tool).update(name='Leonardo')
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
updated = sender.update(fields={'email': 'leonardo.amaral@vtex.com'})
```

Method signatures and behavior match the `Contact` facade.
