# Feature Specification: Flows Client Abstraction

**Feature Branch**: `001-flows-client`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "Preciso criar um client de abstrações de requisições ao flows, para que eu possa criar novas funcionalidades para o toolkit como o broadcasts sem ter que criar um código que faz a requisição ao flows de forma bem manual. Quero poder ter a lógica de fazer a requisição ao flows abstraída em um client, para que seja mais fácil fazer integrações do toolkit ao flows e diminuindo a repetição de código. Não é para mexer em nada presente no diretório broadcasts, nem adicionar integração a nenhum endpoint do flows; nessa task vamos nos ater apenas a criar o client de abstrações e seus testes."

## Clarifications

### Session 2026-06-10

- Q: When the client cannot resolve an authentication token, what should it do? → A: Raise a configuration error before sending the request (fail fast).
- Q: Which HTTP methods should the client support in this iteration? → A: The full standard set — GET, POST, PUT, PATCH, DELETE.
- Q: Should requests have a timeout? → A: No timeout, matching the behavior of existing integrations.
- Q: How should the client handle a success response with an empty body (e.g., 204 No Content)? → A: Treat as success and return an empty result; raise an error only for malformed non-empty bodies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Make an authenticated request to Flows without manual plumbing (Priority: P1)

A toolkit developer building a new feature that integrates with the Flows platform needs to send a request to a Flows endpoint. Instead of manually resolving the base URL, building headers, attaching authentication, serializing the body, issuing the HTTP call, and handling failures — as is done today in the broadcasts feature — they instantiate the Flows client and call a single request operation, providing only the endpoint path and the payload.

**Why this priority**: This is the core value of the feature. Removing the repeated request plumbing is the entire reason the client exists; without it, every new Flows integration duplicates the same boilerplate.

**Independent Test**: Can be fully tested by instantiating the client with a valid configuration source, invoking a request to an arbitrary path with a payload (with the network layer mocked), and verifying the correct URL, headers, authentication, and body were produced and the parsed response was returned.

**Acceptance Scenarios**:

1. **Given** a client configured with a base URL and authentication token, **When** the developer requests an arbitrary Flows path with a payload, **Then** the client issues the request to the correct full URL with the authentication and content headers attached and returns the parsed response.
2. **Given** a client configured with a base URL containing a trailing slash, **When** a request is made to a path, **Then** the resulting URL is well-formed without duplicate slashes.
3. **Given** a successful response from Flows, **When** the request completes, **Then** the developer receives the response data without needing to parse it themselves.

---

### User Story 2 - Resolve configuration automatically from execution context (Priority: P2)

A toolkit developer wants the client to discover its configuration (base URL, authentication token, project identification) the same way existing toolkit features do: from the execution context first, falling back to environment variables, with a sensible default for the base URL. They should not have to write configuration-resolution code for each new integration.

**Why this priority**: Configuration resolution is the second-largest source of duplicated code in current integrations. It depends on the core request capability (P1) being in place to be useful.

**Independent Test**: Can be fully tested by constructing the client with contexts and environments containing configuration values at different priority levels and verifying the client picks the correct value in each case.

**Acceptance Scenarios**:

1. **Given** a configuration value present in both the execution context and the environment, **When** the client resolves configuration, **Then** the context value takes precedence.
2. **Given** no base URL in the context or environment, **When** the client is created, **Then** it falls back to the default Flows base URL.
3. **Given** a required configuration value missing from all sources, **When** the client is created or used, **Then** a configuration error is raised that names the missing value and where it can be provided.

---

### User Story 3 - Receive consistent, typed errors for failed requests (Priority: P3)

A toolkit developer calling Flows through the client needs failures (non-success responses, network problems) surfaced as client-specific errors with enough information to diagnose the problem, so each integration does not implement its own error translation.

**Why this priority**: Error handling completes the abstraction, but the client already delivers value with P1 and P2 alone; integrations could temporarily handle raw failures themselves.

**Independent Test**: Can be fully tested by simulating non-success responses and network failures (with the network layer mocked) and verifying that the client raises its own error types carrying the status and response details.

**Acceptance Scenarios**:

1. **Given** Flows responds with a non-success status, **When** the request completes, **Then** the client raises a client-specific error containing the status code and response body.
2. **Given** the network request fails before a response is received, **When** the failure occurs, **Then** the client raises a client-specific error describing the failure, distinguishable from a configuration error.
3. **Given** any client-specific error, **When** an integration catches the client's base error type, **Then** all failure modes (configuration, HTTP, network) are covered by that single type.

---

### Edge Cases

- What happens when the base URL has a trailing slash or the path lacks a leading slash? The client must normalize and produce a well-formed URL.
- What happens when no authentication token is available? The client fails fast with a configuration error before attempting the request; no unauthenticated request is ever sent.
- How does the client behave when Flows returns a success status with an empty body (e.g., 204 No Content)? It treats the request as successful and returns an empty result.
- How does the client behave when Flows returns a success status but a non-empty body that cannot be parsed? The error raised must indicate the response was unreadable.
- What happens when a request is made with no payload (e.g., a read operation)? The client must support requests without a body.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The client MUST expose a generic request operation that accepts an endpoint path and optional payload and returns the parsed response, without containing knowledge of any specific Flows endpoint. Success responses with an empty body MUST be treated as successful and yield an empty result.
- **FR-002**: The client MUST support the standard request methods GET, POST, PUT, PATCH, and DELETE, so integrations can retrieve, create, update, and remove platform resources.
- **FR-003**: The client MUST resolve its base URL from the execution context first, then environment variables, then a default Flows URL, and MUST normalize it so generated URLs are well-formed.
- **FR-004**: The client MUST resolve the authentication token from the execution context and attach it to outgoing requests as an authorization credential. If no token can be resolved, the client MUST raise a configuration error before any request is sent; it MUST NOT send unauthenticated requests.
- **FR-005**: The client MUST raise a configuration-specific error naming the missing value and its expected sources when a required configuration value cannot be resolved.
- **FR-006**: The client MUST translate non-success responses into a client-specific error carrying the response status and body.
- **FR-007**: The client MUST translate network-level failures into a client-specific error describing the failure.
- **FR-008**: All client errors MUST share a common base error type so integrations can handle all failure modes with a single catch.
- **FR-009**: The client MUST be delivered as a new, self-contained part of the toolkit following the established package layout, with its public API documented.
- **FR-010**: The client MUST be fully covered by automated tests with all network interactions mocked; no real network calls may occur during testing.
- **FR-011**: The existing broadcasts feature MUST NOT be modified in any way by this work.
- **FR-012**: No integration with any specific Flows endpoint may be added as part of this work; the deliverable is the abstraction layer and its tests only.

### Key Entities

- **Flows Client**: The abstraction that owns configuration resolution, request construction, execution, and error translation for communication with the Flows platform.
- **Client Configuration**: The set of values the client needs to operate — base URL, authentication token, and optional project identification — resolved from the execution context, environment, or defaults.
- **Client Errors**: A small hierarchy of failure types — a common base error, a configuration error, and request/response errors — that integrations use to handle failures uniformly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new Flows integration can issue an authenticated request to the platform by writing only the endpoint path and payload — zero lines of URL building, header construction, or error translation code.
- **SC-002**: 100% of the client's request flows (success, configuration failure, non-success response, network failure) are covered by automated tests with no real network calls.
- **SC-003**: The broadcasts directory shows zero changes after the work is complete.
- **SC-004**: All repository quality gates (lint, type check, test suite) pass with the new client included, and overall test coverage does not decrease.

## Assumptions

- The client targets the same Flows platform already used by existing toolkit features, and the existing staging URL is an acceptable default base URL.
- Configuration resolution follows the precedence already established in the toolkit: execution context values (project, then credentials, then globals) before environment variables.
- The authentication scheme is the bearer-token style already used by existing Flows integrations in the toolkit.
- The client is synchronous, matching the execution model of current toolkit features; asynchronous support is out of scope.
- Retry policies, rate limiting, and request timeouts are out of scope for this iteration; the client imposes no timeout, matching the behavior of existing integrations.
- Refactoring the broadcasts feature to use the new client is explicitly out of scope and may be done in a future task.
