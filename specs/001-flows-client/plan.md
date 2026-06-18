# Implementation Plan: Flows Client Abstraction

**Branch**: `001-flows-client` | **Date**: 2026-06-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-flows-client/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create a reusable, endpoint-agnostic HTTP client for the Flows platform inside the `weni` package, so future toolkit integrations (like broadcasts) no longer hand-roll URL building, configuration resolution, authentication headers, and error translation. The client resolves configuration from `Context` → environment → default, exposes generic `get/post/put/patch/delete` request operations via `requests`, raises a typed error hierarchy, and ships with a pytest suite at 100% coverage with all network calls mocked. Nothing in `weni/broadcasts/` is touched and no specific Flows endpoint is integrated.

## Technical Context

**Language/Version**: Python >= 3.10 (per `pyproject.toml`; no syntax beyond 3.10)

**Primary Dependencies**: `requests` (already a runtime dependency); `typing-extensions` available if needed. No new runtime dependencies.

**Storage**: N/A

**Testing**: pytest + pytest-mock + pytest-cov (existing dev dependencies); 100% coverage required for the new module; no real network calls

**Target Platform**: Same as the library — any environment running the toolkit (AWS Lambda tool execution and local development)

**Project Type**: Published Python library (`weni-agents-toolkit`), new domain subpackage

**Performance Goals**: N/A — thin synchronous wrapper around `requests`; no timeout imposed (clarified in spec)

**Constraints**: ruff (line length 119, single quotes, tab indentation), mypy zero errors, complete type annotations, public API docstrings, no changes to `weni/broadcasts/`

**Scale/Scope**: One new subpackage (`weni/flows/`), ~3 source modules + tests; public surface of one client class and a small error hierarchy

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Python Code Quality | Single-responsibility modules, docstrings on public API, ruff format conventions, Python >= 3.10 compatible | PASS — small client class + error module, all public symbols documented |
| II. Static Typing with mypy | Full annotations, `poetry run mypy weni` zero errors, no `Any` in public signatures where precise types exist | PASS — design uses precise types (`Mapping`, `dict[str, Any]` only for JSON payloads, which is the established idiom in the codebase) |
| III. Testing with pytest | Tests colocated in `weni/flows/tests/`, HTTP mocked with pytest-mock, coverage does not decrease (target: 100% for the new module) | PASS — test plan covers success, config failure, HTTP error, network error, URL normalization, empty-body responses |
| IV. Linting with ruff | `poetry run ruff check .` zero violations, no new suppressions | PASS — no rule changes needed |
| V. Consistency with `weni` package structure | New domain as subpackage `weni/flows/` with `__init__.py` exposing public API and `tests/` dir; reuse `Context`; no loose root modules | PASS — fills the existing empty `weni/flows/` placeholder; mirrors `weni/broadcasts/` layout |

**Initial gate evaluation**: PASS — no violations to justify; Complexity Tracking left empty.

**Post-design re-evaluation**: PASS — design artifacts (data-model, contracts) introduce no new dependencies, no structural drift, and no public `Any` beyond JSON payload idioms already used in the codebase.

## Project Structure

### Documentation (this feature)

```text
specs/001-flows-client/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── client-api.md    # Public API contract for the Flows client
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
weni/
└── flows/                       # Existing empty placeholder becomes the new domain subpackage
    ├── __init__.py              # Public API: FlowsClient + error types
    ├── client.py                # FlowsClient: config resolution, request execution
    ├── exceptions.py            # FlowsClientError (base), FlowsClientConfigError,
    │                            # FlowsHTTPError, FlowsNetworkError, FlowsResponseError
    ├── resources/               # Existing empty dir, untouched
    └── tests/
        ├── __init__.py
        ├── test_client.py       # Request execution, URL building, headers, methods, payloads
        ├── test_config.py       # Configuration resolution precedence and failures
        └── test_exceptions.py   # Error hierarchy and error content
```

**Structure Decision**: Single new domain subpackage `weni/flows/`, mirroring the established `weni/broadcasts/` layout (modules + colocated `tests/`). The directory already exists as an empty placeholder with no code or references, so adopting it introduces no breaking change. `weni/broadcasts/` is not modified; whether `weni/__init__.py` re-exports the new subpackage is decided in research.md (R6).

## Complexity Tracking

> No constitution violations — table intentionally left empty.
