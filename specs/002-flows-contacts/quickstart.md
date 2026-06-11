# Quickstart: Validating the Flows Contacts Integration

**Feature**: 002-flows-contacts | **Date**: 2026-06-11

Runnable scenarios proving the feature end-to-end. See [contracts/contacts-api.md](./contracts/contacts-api.md) and [data-model.md](./data-model.md).

## Prerequisites

```bash
poetry install
```

## Quality gates (constitution)

From repository root:

```bash
poetry run ruff check .
poetry run mypy weni
poetry run pytest
```

Expected:

- ruff: zero violations
- mypy: zero errors
- pytest: all tests pass; overall `weni` coverage >= 95%

## Targeted validation — 100% contacts module coverage

```bash
poetry run pytest weni/contacts/tests/ --cov=weni.contacts --cov-report=term-missing
```

Expected: **100%** coverage for all modules under `weni/contacts/` (`contact.py`, `sender.py`, `__init__.py`), no real network calls.

## Scope guards

```bash
git diff main --stat -- weni/broadcasts/   # must show no changes (FR-011)
rg -n "requests\\.(get|post|request)" weni/contacts/  # must match nothing in source (FR-002: FlowsClient only)
```

## Documentation

Verify the public API user guide was added (constitution Development Workflow; tasks T016):

```bash
test -f docs/user-guide/contacts.md
rg -n "contacts" mkdocs.yml   # nav entry for the contacts user guide
```

Expected: `docs/user-guide/contacts.md` exists and `mkdocs.yml` includes a nav link to it.

## Smoke scenarios (mocked transport)

### Get contact by conversation URN

```python
from unittest.mock import MagicMock, patch
from weni.contacts import Contact, ContactSender
from weni.context import Context

ctx = Context(
	credentials={}, parameters={}, globals={},
	contact={'urns': ['whatsapp:5582999893640']},
	project={'auth_token': 'token', 'flows_url': 'https://flows.example.com'},
	constants={},
)

list_response = {
	'results': [{'uuid': 'abc', 'name': 'Leonardo', 'fields': {'email': 'a@b.com'}, 'urns': ['whatsapp:5582999893640']}],
	'next': None, 'previous': None,
}

with patch.object(ContactSender, '_get_client') as mock_client_factory:
	client = MagicMock()
	client.get.return_value = list_response
	mock_client_factory.return_value = client

	sender = ContactSender(ctx)
	contact = sender.get()
	assert contact['uuid'] == 'abc'
	client.get.assert_called_once()
```

Expected: returns unwrapped contact dict; GET called with `urn` query param.

### Update contact fields (update-only)

```python
with patch.object(ContactSender, '_get_client') as mock_client_factory:
	client = MagicMock()
	client.get.return_value = {'results': [{'uuid': 'abc', 'urns': ['whatsapp:5582999893640']}], 'next': None, 'previous': None}
	client.post.return_value = {'uuid': 'abc', 'fields': {'email': 'leonardo.amaral@vtex.com'}}
	mock_client_factory.return_value = client

	sender = ContactSender(ctx)
	updated = sender.update(fields={'email': 'leonardo.amaral@vtex.com'})
	assert updated['fields']['email'] == 'leonardo.amaral@vtex.com'
	client.post.assert_called_once()
```

Expected: GET precedes POST; POST body contains only supplied fields; no create when GET would fail.

### Validation — reject `urns` in body

```python
from weni.contacts import ContactValidationError
import pytest

sender = ContactSender(ctx)
with pytest.raises(ContactValidationError):
	sender.update(urns=['tel:+123'])
```

Expected: raises before any Flows call.

### Facade usage in a tool

```python
from weni.contacts import Contact

# Inside Tool.execute:
# contact = Contact(self).get()
# Contact(self).update(fields={'email': user_email})
```

Expected: no manual FlowsClient setup required.
