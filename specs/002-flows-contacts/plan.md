# Implementation Plan: Flows Contacts Integration

**Branch**: `002-flows-contacts` | **Date**: 2026-06-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-flows-contacts/spec.md`

**Note**: User planning guidance: mirror `weni/broadcasts/` structure, use `weni/flows` client in the sender, pytest suite with **100% module coverage** for the new package.

## Summary

Add a new `weni/contacts/` domain package that lets toolkit developers **get** and **update** a Flows contact by conversation URN during tool execution. The public surface follows the broadcasts pattern (`Contact` facade bound to a `Tool`, `ContactSender` for HTTP semantics). Unlike `BroadcastSender`, `ContactSender` delegates all transport to `FlowsClient` — no manual `requests` plumbing. Behavior includes update-only semantics (existence check before POST), WhatsApp Brazil 9th-digit URN retry on lookup, hybrid update payloads (dict + kwargs with kwargs precedence), and validation that rejects `urns` in the body when the contact is identified by query URN. Ship colocated pytest tests with **100% coverage** on `weni/contacts/` (all Flows calls mocked). Do not modify `weni/broadcasts/`.

## Technical Context

**Language/Version**: Python >= 3.10 (per `pyproject.toml`; no syntax beyond 3.10)

**Primary Dependencies**: `weni.flows.FlowsClient` (mandated transport); `requests` only indirectly via the client. No new runtime dependencies.

**Storage**: N/A

**Testing**: pytest + pytest-mock + pytest-cov; **100% line coverage required for `weni/contacts/`**; no real network calls; overall `weni` coverage must remain >= 95% (constitution floor)

**Target Platform**: Same as the library — AWS Lambda tool execution and local development

**Project Type**: Published Python library (`weni-agents-toolkit`), new domain subpackage

**Performance Goals**: N/A — synchronous thin wrapper; two HTTP calls on update (GET existence check + POST write); no timeout (inherits Flows client behavior)

**Constraints**: ruff (line length 119, single quotes, tab indentation per flows client / project convention in new code), mypy zero errors, complete type annotations, public API docstrings, broadcasts package untouched

**Scale/Scope**: One new subpackage (`weni/contacts/`), ~3 source modules + tests; public surface of one facade class, one sender class, and a small error hierarchy

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Python Code Quality | Single-responsibility modules, docstrings on public API, ruff format conventions, Python >= 3.10 compatible | PASS — facade + sender + errors; sender owns contacts endpoint semantics, client owns transport |
| II. Static Typing with mypy | Full annotations, `poetry run mypy weni` zero errors, no unnecessary `Any` in public signatures | PASS — JSON payloads as `dict[str, Any]` matches established idiom; return type `dict[str, Any]` for Flows contact objects |
| III. Testing with pytest | Tests colocated in `weni/contacts/tests/`, HTTP mocked, **100% coverage for new module**, overall >= 95% | PASS — test matrix enumerated in research.md R7; mirrors `weni/broadcasts/tests/` and `weni/flows/tests/` patterns |
| IV. Linting with ruff | `poetry run ruff check .` zero violations | PASS — no rule changes |
| V. Consistency with `weni` package structure | New domain subpackage with `__init__.py` + `tests/`; reuse `Context` and `FlowsClient`; mirror broadcasts layout | PASS — `contact.py` + `sender.py` parallel to `broadcast.py` + `sender.py` |

**Initial gate evaluation**: PASS — no violations to justify.

**Post-design re-evaluation**: PASS — contracts and data model introduce no new dependencies, no structural drift, and no changes outside `weni/contacts/`.

## Project Structure

### Documentation (this feature)

```text
specs/002-flows-contacts/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── contacts-api.md  # Public API contract
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
weni/
└── contacts/                    # NEW domain subpackage
    ├── __init__.py              # Public API: Contact, ContactSender, error types
    ├── contact.py               # Contact facade (mirrors broadcast.py)
    ├── sender.py                # ContactSender: URN resolution, get/update, FlowsClient
    └── tests/
        ├── __init__.py
        ├── conftest.py          # create_context helper (mirrors broadcasts/flows tests)
        ├── test_contact.py      # Facade delegation to sender
        └── test_sender.py       # URN resolution, get, update, errors, 9th-digit retry
```

**Structure Decision**: Single new subpackage `weni/contacts/` mirroring `weni/broadcasts/` (facade + sender + colocated tests) while using `FlowsClient` from `weni/flows/` instead of raw `requests`. No `messages.py` equivalent — contacts operations work on plain dict payloads returned by Flows. Root `weni/__init__.py` is not modified in this iteration (same deferral as flows client — subpackage import path only).

## Complexity Tracking

> No constitution violations — table intentionally left empty.
