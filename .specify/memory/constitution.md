<!--
Sync Impact Report
- Version change: 1.1.0 → 2.0.0 (MAJOR)
- Reason for MAJOR: the root engineering constitution redefines rules this document already
  had — commit messages move from SHOULD (`feat:`, `fix:`, `tests:`, `build:`) to MUST
  Conventional Commits with types `feat|fix|docs|refactor|test|chore`, and CHANGELOG.md must
  follow Keep a Changelog categories. Root prevails over the previous project rules.
- Modified principles:
  - I. Python Code Quality → I. Python Code Quality and Explicitness (absorbs backend
    "Explicit Over Clever": no hidden side effects, named constants for meaningful
    literals, comments explain why)
  - III. Testing with pytest (NON-NEGOTIABLE): adds backend "Tests Exercise Flows" — every
    flow needs an input-to-effect test covering success and failure paths
  - V. Consistency with the `weni` Package Structure: new Flows integrations MUST use
    `FlowsClient`; breaking-change rule moved to VI
- Added principles:
  - VI. Versioned Public Contracts (root)
  - VII. Changelog Maintenance (root)
  - VIII. Never Trust External Input (backend)
  - IX. Fail Gracefully and Predictably (backend)
  - X. Bounded Retry Over REST (backend)
  - XI. Stateless Execution and Peak Load (backend)
  - XII. Observability and Diagnosable Errors (root Observability + backend Diagnosable Errors)
  - XIII. Security and Secrets (root)
  - XIV. Specification Traceability (root)
  - XV. No Silent Divergence (root)
  - XVI. Version Control and Review (root)
  - XVII. Contained Changes (backend; absorbs the previous "dedicated PR" rules for lint
    config and gate tooling upgrades)
  - XVIII. Commit Messages (root)
- Added sections: none (Quality Gates and Development Workflow rewritten)
- Removed sections: none
- Templates requiring updates:
  - ⚠ .specify/templates/spec-template.md: lacks the mandatory "Inheritance from Product
    Spec" opening section (XIV) and a peak-load declaration (XI); not edited by this run
  - ⚠ .specify/extensions/git/git-config.yml: auto-commit messages use "[Spec Kit] ..."
    which violates XVIII; not edited by this run
  - ✅ .specify/templates/plan-template.md: Constitution Check gates resolved at runtime
  - ✅ .specify/templates/tasks-template.md: test tasks per story already supported
- Follow-up TODOs:
  - TODO(BRANCH_PROTECTION): confirm GitHub branch protection on `main` requires one approval
    and a green CI run and blocks direct pushes (XVI); could not be verified locally
  - TODO(COVERAGE_GATE): `.github/workflows/ci.yml` does not enforce the 95% floor
    (no `--cov-fail-under=95`) (III)
  - TODO(DEPENDENCY_AUDIT): no dependency vulnerability check runs in CI (XIII)
  - TODO(HTTP_TIMEOUTS): `weni/flows/client.py` (`_send`) and `weni/broadcasts/sender.py`
    call `requests` without `timeout=` (IX)
  - TODO(RETRY_POLICY): no bounded retry exists for Flows calls; broadcast `POST` needs a
    deduplication key before it can be retried (X)
  - TODO(TRACE_REDACTION): `weni/tracing/tracer.py` `_serialize_value` serializes public
    attributes of any object, so a traced method receiving `Context` records
    `credentials`, `project['auth_token']`, and contact PII (XII, XIII)
  - TODO(ERROR_PII): `FlowsHTTPError` embeds the raw Flows response body (may contain
    contact names, URNs, fields) in its message (XII)
  - TODO(ERROR_IDENTIFIERS): `Context` defines no account or correlation identifier; decide
    their source before XII can be fully met
  - TODO(CHANGELOG_FORMAT): CHANGELOG.md entries since 2.3.2 are flat lists without Keep a
    Changelog categories; new entries MUST comply (VII)
  - TODO(SPEC_INHERITANCE): `specs/001-flows-client` and `specs/002-flows-contacts` predate
    XIV and have no product spec inheritance; decide backfill or grandfathering

Provenance:
- Source: weni-ai/vtex-cx-engineering-constitutions (main), fetched 2026-10-01
- Files: base-constitution.md, backend/base-constitution.md
- Domains: backend
- Project layer: previous .specify/memory/constitution.md v1.1.0, pyproject.toml,
  .github/workflows/, README.md, CHANGELOG.md, weni/
-->

# Weni Agents Toolkit Constitution

## Core Principles

### I. Python Code Quality and Explicitness

Code MUST be clear, small, and purposeful. Functions and classes MUST have a single
responsibility and descriptive names. Public APIs (anything importable from `weni` or its
subpackages) MUST have docstrings describing purpose, parameters, and return values.
Dead code, commented-out blocks, and speculative abstractions MUST NOT be merged.

What a piece of code does MUST be evident where it happens: hidden side effects and implicit
control flow MUST NOT be introduced to save lines. Any literal that carries meaning — a URL,
a threshold, a limit, a timeout, a retry count — MUST be a named constant (as
`FlowsClient.DEFAULT_FLOWS_URL` is) rather than an inline value; a literal with no meaning
beyond its own value, such as an index of 0 or an increment of 1, is exempt. Comments MUST
explain why a decision was made — the constraint, the trade-off, or the non-obvious reason; a
comment that restates what the code says SHOULD be resolved by rewriting the code.

Line length is 119 characters and formatting follows the `ruff format` configuration in
`pyproject.toml` (single quotes, tab indentation). Compatibility with Python >= 3.10 MUST be
preserved; syntax beyond 3.10 MUST NOT be used.

**Rationale**: this is a published PyPI library (`weni-agents-toolkit`) whose public surface
is consumed by external agents, and it is read far more often than written, usually by
someone without the original context. An unexplained literal is a decision nobody can
review, and clarity and stability outweigh cleverness.

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
contract changes.

Every flow — a use case reachable from the public API, such as a `Tool` execution that reads
and updates a contact through `Contact` → `ContactSender` → `FlowsClient` — MUST have at
least one test covering it from input to resulting effect (the outbound request built and the
value returned or error raised), mocking only at the external boundary. Every flow MUST cover
its success path and its failure paths (invalid input, HTTP error, network failure); an error
path that no test exercises MUST NOT be considered covered. Tests that assert a single method
in isolation SHOULD be used for edge cases and input variations, but MUST NOT be the only
coverage a flow has.

`poetry run pytest` MUST pass before merge. Total test coverage (measured with `pytest-cov`
over `weni`) MUST be at least 95% and MUST NOT decrease relative to the base branch; a PR that
drops coverage below 95% MUST NOT be merged until tests restore the floor. External services
(HTTP, Lambda, platform APIs) MUST be mocked with `pytest-mock`; tests MUST NOT perform real
network calls.

**Rationale**: the library runs inside user-facing conversational agents, so regressions reach
production conversations directly. A suite made only of isolated method tests can be green
while the composition is broken, and failure paths are the least exercised in development and
the most expensive in production.

### IV. Linting with ruff

`poetry run ruff check .` MUST pass with zero violations before merge. Lint rules are
configured centrally in `pyproject.toml`; per-file or inline suppressions (`# noqa`) MUST
be justified with a comment and scoped to a specific rule. Lint configuration changes MUST
be proposed in a dedicated PR, not bundled with feature work (see XVII).

**Rationale**: a single enforced lint baseline keeps the codebase uniform across
contributors and removes style debates from code review.

### V. Consistency with the `weni` Package Structure

New functionality MUST follow the established package layout: one subpackage per domain
under `weni/` (e.g. `broadcasts/`, `components/`, `contacts/`, `context/`, `events/`,
`flows/`, `responses/`), each with its own `__init__.py` exposing the public API and a
`tests/` directory. New domains MUST be introduced as new subpackages, not as loose modules at
the root. Existing patterns — `Tool`/`Skill` execution via `Context`, typed response classes,
component-based messages — MUST be reused and extended rather than duplicated or bypassed.
New integrations with the Flows platform MUST issue their requests through
`weni.flows.FlowsClient`, so that timeouts, retries, and error translation (IX, X) live in one
place.

**Rationale**: consumers rely on predictable import paths and idioms; structural drift
multiplies maintenance cost and breaks downstream agents.

### VI. Versioned Public Contracts

The public contract of this library is everything importable from `weni` and its
subpackages, plus the shape of the results it hands to the Weni platform (responses,
components, events, and traces). Any change to it MUST be versioned following SemVer through
the `version` field in `pyproject.toml`: MAJOR for breaking changes, MINOR for
backward-compatible additions, PATCH for fixes. Changes MUST be backward compatible or ship
with an announced deprecation path: the old API keeps working, emits a `DeprecationWarning`
naming its replacement (via `typing_extensions.deprecated`, as in `weni/events/event.py`), is
listed under `Deprecated` in `CHANGELOG.md`, and is removed only in a later MAJOR. Silent
breaking changes MUST NOT be introduced; every breaking change MUST be justified in its PR and
engineering spec.

**Rationale**: agents built on the toolkit pin it from PyPI and depend on stable contracts;
explicit versioning and deprecation give them a predictable path to adapt without broken
conversations in production.

### VII. Changelog Maintenance

`CHANGELOG.md` MUST follow the Keep a Changelog format. Every user-facing change MUST appear
under its release heading (`## [X.Y.Z] - YYYY-MM-DD`) in the appropriate category: `Added`,
`Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. The release heading MUST match the
`pyproject.toml` version and the git tag that triggers `.github/workflows/cd.yml` to publish
to PyPI. Entries SHOULD describe the impact for consumers rather than repeat commit subjects.
When the public API changes, the relevant README or `docs/` pages MUST be updated in the same
change.

**Rationale**: the changelog is the release documentation PyPI consumers read before
upgrading; SemVer alignment between changelog, `pyproject.toml`, and tag keeps upgrade
expectations predictable.

### VIII. Never Trust External Input

Everything that reaches toolkit code from outside it MUST be treated as potentially
malicious, incomplete, or incorrect until validated: tool parameters (often filled by an LLM
from conversation text), contact, project, and globals data in `Context`, and payloads
returned by platform or third-party APIs. Every such input MUST be validated for type,
format, range, and business rules where it enters toolkit code, before it is used to build a
request or a response, failing with a typed error before any outbound call (as
`weni.contacts` does for an empty payload or `urns` in the body). Authorization belongs to
the APIs the toolkit calls: every outbound request MUST carry the project's credentials, and a
local check MUST NOT be used to replace or skip server-side authorization.

**Rationale**: conversation content is user-controlled and can be crafted to inject values
into Flows requests or corrupt contact records. Validating at entry stops that before it
leaves the process, while server-side authorization remains the only check that cannot be
bypassed.

### IX. Fail Gracefully and Predictably

Every outbound network call made by toolkit code MUST set an explicit timeout defined as a
named constant and MUST NOT block indefinitely; a `requests` call without `timeout=` MUST NOT
be merged. Failures MUST be handled explicitly and surfaced through the integration's typed
error hierarchy (e.g. `FlowsClientError` and its subclasses `FlowsClientConfigError`,
`FlowsHTTPError`, `FlowsNetworkError`, `FlowsResponseError`) — never as an unhandled
`requests` exception, a bare `Exception`, or a message that leaks tokens, headers, or internal
details.

**Rationale**: tools run inside a time-bounded Lambda execution in the middle of a live
conversation; one hanging dependency consumes the whole budget and the user gets no answer.
Typed, predictable errors let the agent decide how to recover instead of crashing.

### X. Bounded Retry Over REST

When toolkit code propagates data to another service over REST (e.g. sending a broadcast or
updating a Flows contact), a failed call MUST be retried rather than dropped. A retry MUST be
attempted only for failures that could succeed on another attempt — a connection error, a
request timeout, an HTTP 5xx, or an HTTP 429 — and MUST NOT be attempted on a 4xx that
reflects a defect in the request itself. A retry MUST only be applied to an operation that is
idempotent (by HTTP semantics or because it sets absolute values, as a contact field update
does) or protected by a deduplication key; a non-idempotent operation such as a broadcast
`POST` MUST be made idempotent rather than left without retry. Every retry policy MUST define a
maximum number of attempts and a backoff strategy as named constants; unbounded retry MUST NOT
be used, and the worst-case total duration SHOULD fit inside the tool's execution budget.
When attempts are exhausted, the failure MUST be logged and MUST reach the caller as a typed
error so the agent can recover; it MUST NOT be silently discarded.

**Rationale**: propagation between services fails for transient reasons far more often than
permanent ones, so retrying keeps Flows and the agent consistent. Retrying a rejected request
or a non-idempotent operation multiplies load or duplicates effects, unbounded retry amplifies
an outage, and an exhausted retry that is swallowed makes data disappear between two systems
that each believe they succeeded.

### XI. Stateless Execution and Peak Load

Toolkit code MUST be stateless across executions so that the host runtime can scale
horizontally. The Lambda process is reused between warm starts, so state that outlives a
single tool, rule, or preprocessor execution MUST NOT be kept in module globals, class
attributes, or local disk (`/tmp`); it MUST live in an external store shared by all instances
(for example, Flows contact fields). Per-execution state — events, traces, messages sent —
MUST be scoped to the execution instance, as `Tool` already does for events. Every engineering
spec MUST declare the peak load its feature is expected to sustain, stated as peak and not as
average — for this library, the peak rate of executions and of outbound requests the feature
drives against platform APIs such as Flows.

**Rationale**: state leaked between warm starts mixes data across conversations and makes
scaling out unsafe. Sizing for average traffic guarantees failure during sales peaks, and a
declared peak turns capacity into a number that can be reviewed and tested.

### XII. Observability and Diagnosable Errors

Logs emitted by toolkit code MUST be structured. Logs, execution traces (`weni.tracing`),
events, and exception messages MUST NOT contain secrets — `context.credentials`,
`context.project['auth_token']`, Authorization headers — or sensitive personal data: contact
names, URNs (they embed phone numbers), e-mail addresses, or government identifiers. Errors
MUST be traceable across components through a correlation identifier.

Every error report the toolkit produces — the `error`/`error_summary` of an execution trace
and the typed exceptions it surfaces to the host runtime, which forwards them to error
tracking — MUST carry enough context to be located and filtered without reproducing it: at
minimum the project identifier (`context.project['uuid']`), the account identifier, the user
identifier, and the correlation identifier of the execution. Those identifiers MUST be opaque:
the contact UUID, never the URN.

**Rationale**: an error without identifying context can be counted but not investigated, while
an error that carries a phone number or token creates a new data-exposure incident. Opaque
identifiers give exactly the filtering an investigation needs and keep reports free of
personal data.

### XIII. Security and Secrets

Secrets MUST never be committed to the repository, including tests, documentation examples,
and `specs/`; test fixtures MUST use obviously fake values. At runtime, secrets MUST reach
toolkit code only through what the platform injects (`context.credentials`,
`context.project`, or environment variables) and MUST NOT have hard-coded defaults; CI secrets
(`PYPI_TOKEN`, `CODECOV_TOKEN`) MUST live in GitHub Actions secrets. Access MUST follow least
privilege: a credential read from `Context` MUST be sent only to the service it belongs to.
Dependencies MUST come only from PyPI through Poetry, MUST stay pinned in `poetry.lock`, and
MUST be checked for known vulnerabilities before merge.

**Rationale**: the toolkit handles project tokens and third-party credentials on behalf of
every agent built with it; one leaked or misrouted token compromises a whole project.
Prevention is far cheaper than remediation.

### XIV. Specification Traceability

Every engineering spec (`specs/<NNN-feature>/spec.md`) MUST derive from exactly one approved
product spec and MUST reference it through an immutable, pinned version (commit or tag); a
mutable URL or ID alone MUST NOT be used. The product spec MUST exist and be tagged before its
engineering spec is created. An engineering spec MUST NOT redefine the "what" it inherits:
problem, scope, success criteria, and binding decisions belong to the product spec. A
technical architecture document SHOULD be produced for non-trivial features; when it exists it
MUST be linked from the engineering spec, also pinned by commit/tag, but its absence MUST NOT
block the engineering spec.

Every engineering spec MUST open with an inheritance section in exactly this format:

```
## Inheritance from Product Spec
- Product Spec: <title> — <URL>
- Pinned version: <commit/tag>
- Architecture doc: <none | URL + commit/tag>
- Inherited binding decisions: <short list>
- Scope of this spec: <slice implemented by this repo>
- Divergences: <none | link to amendment>
```

**Rationale**: pinning the product spec version guarantees every team implements the same
version of a feature instead of divergent readings of a spec that changed mid-flight. Making
the product spec mandatory prevents engineering work without an agreed problem, and a single
inheritance format keeps the link machine-checkable across repositories.

### XV. No Silent Divergence

When a technical need contradicts something inherited from the product spec — scope, success
criteria, or a binding decision — the divergence MUST NOT be implemented silently in code. It
MUST be raised as an amendment in the product repository and recorded in the `Divergences`
field of the engineering spec's inheritance section, linking to that amendment. Once the
amendment is approved and produces a new tag, the engineering spec's `Pinned version` MUST be
updated to it. A technical difference that contradicts nothing inherited is an implementation
decision, not a divergence, and MUST be recorded in the engineering spec or plan.

**Rationale**: with the product spec as the single source of truth, a silent code deviation
makes intent and implementation drift apart with no audit trail. Routing divergences through
amendments keeps every decision traceable to an agreed change.

### XVI. Version Control and Review

All code MUST enter `main` through a pull request. A merge MUST require at least one approved
review and a green run of `.github/workflows/ci.yml` across the supported Python matrix
(3.10–3.13). Direct pushes to `main` MUST be blocked via GitHub branch protection. `main` MUST
remain releasable at all times. Reviewers MUST verify compliance with this constitution and
flag violations explicitly rather than approving with reservations.

**Rationale**: the policy is only real when the platform enforces it. Peer review and a
protected `main` keep history auditable and stop unreviewed changes from being tagged and
published to PyPI.

### XVII. Contained Changes

A change MUST be limited to the context it was asked to address. Refactoring, renaming,
reformatting (including `ruff format` over untouched files), lint or tooling configuration
changes, gate tooling upgrades (ruff, mypy, pytest), and behavior adjustments outside that
context MUST NOT ride along; each belongs to its own PR. This principle governs the scope of a
change as a whole; XVIII governs how it is divided into commits, and a change that stays in
scope MAY span several commits.

**Rationale**: a change that reaches beyond its stated scope is a change nobody reviewed on
purpose. It hides the intended fix inside unrelated edits and turns a revert into a choice
between losing the fix and keeping an unrelated regression.

### XVIII. Commit Messages

Commits MUST follow Conventional Commits format: `<type>: <description>`. Allowed types:
`feat`, `fix`, `docs`, `refactor`, `test`, `chore`. The description MUST be imperative,
specific, and no longer than 50 characters. Commits MUST be atomic: one logical change per
commit. The previously used `tests:` and `build:` types MUST NOT be used; use `test:` for test
changes and `chore:` for version bumps, releases, and build changes.

**Rationale**: conventional commits enable automated changelog generation and semantic
versioning; atomic commits simplify bisecting, reverting, and reviewing.

## Quality Gates

The following gates MUST pass locally and in CI before any merge to `main`:

1. `poetry run ruff check .` — zero violations (IV)
2. `poetry run mypy weni` — zero errors (II)
3. `poetry run pytest` — all tests pass, total coverage >= 95% and not decreasing (III)
4. Dependency vulnerability check — no known vulnerabilities in `poetry.lock` (XIII)
5. At least one approved review (XVI)

A PR that fails any gate MUST NOT be merged, regardless of urgency. Gate tooling versions are
pinned by `poetry.lock`; upgrades MUST land in dedicated PRs so that rule changes are
reviewable in isolation (XVII).

## Development Workflow

- Features follow the Spec Kit flow (specify → clarify → plan → tasks → implement) in
  sequentially numbered directories `specs/NNN-feature/` on matching feature branches; each
  spec opens with the inheritance section (XIV) and declares its peak load (XI).
- Releases: bump `version` in `pyproject.toml` (VI), add the `CHANGELOG.md` entry (VII), merge
  to `main`, then push a tag equal to the version (`X.Y.Z`, or `X.Y.ZaN` for pre-releases);
  `.github/workflows/cd.yml` builds, publishes to PyPI, and creates the GitHub release.
- Every user-visible change updates `CHANGELOG.md` and, when the public API changes, the README
  or `docs/` pages (VII).

## Governance

This constitution supersedes ad-hoc practices for all work in this repository. It is
synthesized from the VTEX CX root engineering constitution and the backend constitution
(`weni-ai/vtex-cx-engineering-constitutions`), instantiated for this library. On conflict,
precedence is root engineering constitution > backend constitution > project-specific rules;
a project rule MAY specialize a base article but MUST NOT weaken it unless the exception and
its justification are stated in the article itself.

Spec Kit artifacts (specs, plans, tasks) MUST be checked against these principles. The
plan-phase Constitution Check gate MUST cite the specific principle by number for any flagged
violation; unjustifiable violations MUST be simplified out of the design before
implementation, and justified ones MUST be recorded in the plan's Complexity Tracking table.
`/speckit-analyze` treats any conflict with a MUST as CRITICAL.

Amendments are made by editing `.specify/memory/constitution.md` in a dedicated PR that
documents the motivation and migration impact. Changes to the base constitutions are pulled by
re-running `setup-engineering`, not by hand-editing base-derived text. Versioning of this
document follows SemVer: MAJOR for principle removals or redefinitions, MINOR for new or
materially expanded principles or sections, PATCH for clarifications and wording fixes.
Compliance is reviewed continuously in code review and at each Spec Kit phase gate.

**Version**: 2.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-10-01
