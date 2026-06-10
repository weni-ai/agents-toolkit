<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Modified principles: n/a (initial ratification)
- Added sections:
  - Core Principles (I–V)
  - Quality Gates
  - Development Workflow
  - Governance
- Removed sections: none (template placeholders replaced)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check gates resolved at runtime; no edit needed)
  - ✅ .specify/templates/spec-template.md (no constitution-specific sections required)
  - ✅ .specify/templates/tasks-template.md (test-first ordering already supported)
- Follow-up TODOs: none
-->

# Weni Agents Toolkit Constitution

## Core Principles

### I. Python Code Quality

Code MUST be clear, small, and purposeful. Functions and classes MUST have a single
responsibility and descriptive names. Public APIs (anything importable from `weni` or its
subpackages) MUST have docstrings describing purpose, parameters, and return values.
Dead code, commented-out blocks, and speculative abstractions MUST NOT be merged.
Line length is 119 characters, formatting follows the `ruff format` configuration in
`pyproject.toml` (single quotes, tab indentation). Compatibility with Python >= 3.10 MUST
be preserved; new syntax beyond 3.10 MUST NOT be used.

**Rationale**: this is a published PyPI library (`weni-agents-toolkit`); its public surface
is consumed by external agents and tools, so clarity and stability outweigh cleverness.

### II. Static Typing with mypy (NON-NEGOTIABLE)

All new and modified code MUST carry complete type annotations on function signatures,
class attributes, and return types. `poetry run mypy weni` MUST pass with zero errors before
merge. `# type: ignore` MUST be used only as a last resort, MUST be scoped to a specific
error code (e.g. `# type: ignore[arg-type]`), and MUST include an adjacent comment
explaining why it is unavoidable. `Any` MUST NOT be introduced in public signatures when a
precise type (including `typing-extensions` constructs) is expressible.

**Rationale**: the toolkit advertises type-safe components; typing is part of the product
contract, not an internal convenience.

### III. Testing with pytest (NON-NEGOTIABLE)

Every behavior change MUST be covered by pytest tests colocated in the module's `tests/`
directory (e.g. `weni/broadcasts/tests/`), following the existing layout. Tests MUST be
written for new features, bug fixes (regression test reproducing the bug first), and
contract changes. `poetry run pytest` MUST pass before merge, and coverage (measured with
`pytest-cov` over `weni`) MUST NOT decrease relative to the base branch. External services
(HTTP, Lambda, platform APIs) MUST be mocked with `pytest-mock`; tests MUST NOT perform
real network calls.

**Rationale**: the library runs inside user-facing conversational agents; regressions reach
production conversations directly and are expensive to detect after release.

### IV. Linting with ruff

`poetry run ruff check .` MUST pass with zero violations before merge. Lint rules are
configured centrally in `pyproject.toml`; per-file or inline suppressions (`# noqa`) MUST
be justified with a comment and scoped to a specific rule. Lint configuration changes MUST
be proposed in a dedicated PR, not bundled with feature work.

**Rationale**: a single enforced lint baseline keeps the codebase uniform across
contributors and removes style debates from code review.

### V. Consistency with the `weni` Package Structure

New functionality MUST follow the established package layout: one subpackage per domain
under `weni/` (e.g. `broadcasts/`, `components/`, `context/`, `events/`, `flows/`,
`responses/`), each with its own `__init__.py` exposing the public API and a `tests/`
directory. New domains MUST be introduced as new subpackages, not as loose modules at the
root. Existing patterns — `Tool`/`Skill` execution via `Context`, typed response classes,
component-based messages — MUST be reused and extended rather than duplicated or bypassed.
Breaking changes to public APIs MUST be justified, documented in `CHANGELOG.md`, and
reflected in a semantic version bump in `pyproject.toml`.

**Rationale**: consumers rely on predictable import paths and idioms; structural drift
multiplies maintenance cost and breaks downstream agents.

## Quality Gates

The following gates MUST pass locally and in CI before any merge to the main branch:

1. `poetry run ruff check .` — zero violations
2. `poetry run mypy weni` — zero errors
3. `poetry run pytest` — all tests pass, coverage does not decrease

A PR that fails any gate MUST NOT be merged, regardless of urgency. Gate tooling versions
are pinned by `poetry.lock`; upgrades to ruff/mypy/pytest MUST be done in dedicated PRs so
that rule changes are reviewable in isolation.

## Development Workflow

- Work happens on feature branches; the main branch MUST remain releasable at all times.
- Commits SHOULD follow the existing convention (`feat:`, `fix:`, `tests:`, `build:`).
- Every user-visible change MUST update `CHANGELOG.md` and, when the public API changes,
  the relevant README or docs sections.
- Version bumps in `pyproject.toml` follow semantic versioning: MAJOR for breaking API
  changes, MINOR for new backwards-compatible features, PATCH for fixes.
- Code review MUST verify compliance with this constitution; reviewers MUST flag
  violations explicitly rather than approving with reservations.

## Governance

This constitution supersedes ad-hoc practices for all work in this repository. Spec Kit
artifacts (specs, plans, tasks) MUST be checked against these principles; the plan-phase
Constitution Check gate MUST cite the specific principle for any flagged violation, and
unjustifiable violations MUST be simplified out of the design before implementation.

Amendments are made by editing `.specify/memory/constitution.md` in a dedicated PR that
documents the motivation and migration impact. Versioning of this document follows
semantic versioning: MAJOR for principle removals or redefinitions, MINOR for new or
materially expanded principles/sections, PATCH for clarifications and wording fixes.
Compliance is reviewed continuously in code review and at each Spec Kit phase gate.

**Version**: 1.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
