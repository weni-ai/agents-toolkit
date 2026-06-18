# Quickstart: Validating the Flows Client Abstraction

**Feature**: 001-flows-client | **Date**: 2026-06-10

Runnable scenarios that prove the feature works end-to-end. See [contracts/client-api.md](./contracts/client-api.md) for the API surface and [data-model.md](./data-model.md) for configuration precedence.

## Prerequisites

```bash
poetry install
```

## Quality gates (constitution)

All three must pass from the repository root:

```bash
poetry run ruff check .
poetry run mypy weni
poetry run pytest
```

Expected outcomes:

- ruff: zero violations
- mypy: zero errors
- pytest: all tests pass; coverage report shows `weni/flows/client.py` and `weni/flows/exceptions.py` at **100%**, and overall `weni` coverage has not decreased

## Targeted validation

Run only the new module's suite:

```bash
poetry run pytest weni/flows/tests/ --cov=weni.flows --cov-report=term-missing
```

Expected: 100% coverage for `weni.flows`, no real network calls (the suite must pass with networking disabled).

## Scope guards

Confirm the feature's scope boundaries were respected:

```bash
git diff main --stat -- weni/broadcasts/   # must output nothing (FR-011 / SC-003)
rg -n "whatsapp_broadcasts|api/v2" weni/flows/  # must match nothing outside tests (FR-012: endpoint-agnostic)
```

## Smoke scenario (interactive, optional)

In a Python shell with mocked transport — mirrors acceptance scenarios from the spec:

```python
from unittest.mock import patch
from weni.context import Context
from weni.flows import FlowsClient, FlowsClientConfigError

ctx = Context(
	credentials={}, parameters={}, globals={},
	contact={}, project={'auth_token': 'token', 'flows_url': 'https://flows.example.com/'},
	constants={},
)

client = FlowsClient(ctx)            # resolves config; trailing slash normalized
# client.post('/api/v2/anything.json', json={'k': 'v'})  -> issues POST with Bearer header (mock transport to inspect)

Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
# FlowsClient(<context without auth_token>) -> raises FlowsClientConfigError (fail fast, Q1)
```

Expected: construction succeeds with token present; raises `FlowsClientConfigError` naming `auth_token` when absent.
