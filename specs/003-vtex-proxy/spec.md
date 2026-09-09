# Feature Specification: VTEX Proxy Integration

**Feature Branch**: `003-vtex-proxy`

**Created**: 2026-09-08

**Status**: Draft

**Input**: User description: "Add a VTEX proxy integration to the agents toolkit so gallery-agent tools can call VTEX private APIs the same way they already call Flows contacts (`self.contact.get()`). The v1 surface is `self.vtex.request(...)` plus the shorthand `self.gallery_vtex(...)`. Traffic goes through Retail's generic VTEX proxy (`POST /vtex/proxy/`); payment-gateway and payment-transaction proxies are out of scope. Reuse `context.project.auth_token`. Resolve `retail_url` from context/environment with no hardcoded default."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Call a VTEX private API from a tool without hand-rolling HTTP (Priority: P1)

A toolkit developer building a gallery agent needs to read or write VTEX data during tool execution — for example, listing OMS orders. Today they would have to know the Retail host, assemble a Bearer token, and post a proxy payload themselves. They instead call a single VTEX operation with the VTEX path, HTTP method, and optional headers, body, and query parameters. The integration authenticates with the project token already present in the execution context, forwards the request through the existing Retail VTEX proxy, and returns the parsed VTEX payload.

**Why this priority**: This is the entire product value of v1. Without a single-call proxy, gallery tools keep reinventing authentication and URL construction for every VTEX endpoint.

**Independent Test**: Can be fully tested by constructing an execution context with a project auth token and a Retail base URL, invoking the request operation against a mocked Retail proxy, and verifying the outbound body carries the VTEX method/path (and optional headers, data, params, merchant name) and that the parsed JSON result is returned to the caller.

**Acceptance Scenarios**:

1. **Given** an execution context with a project auth token and a Retail base URL, **When** the developer requests a VTEX path with method `GET`, **Then** the integration posts to the Retail VTEX proxy with that method and a normalized VTEX path, and returns the parsed JSON body.
2. **Given** optional headers, JSON body, query parameters, and merchant name, **When** the developer includes them on the request, **Then** only the provided optional fields are forwarded in the proxy payload.
3. **Given** a VTEX path without a leading slash (for example `api/oms/pvt/orders`), **When** the request is sent, **Then** the path is normalized to start with `/` before it leaves the toolkit.
4. **Given** Retail returns a JSON object or a JSON array, **When** the request succeeds, **Then** the developer receives that value as-is (OMS list endpoints commonly return arrays).
5. **Given** the developer uses either the namespaced `request` operation or the `gallery_vtex` shorthand, **When** they pass the same arguments (path via `path` or `endpoint`), **Then** both styles produce the same outbound proxy call.

---

### User Story 2 - Fail fast with typed, actionable errors (Priority: P2)

A toolkit developer needs to distinguish configuration mistakes (missing token or Retail URL), invalid arguments (unsupported method, empty or absolute path), Retail/VTEX HTTP failures, network failures, and unreadable success bodies. Each failure must raise before or instead of a successful-looking result, so the agent can surface a useful error rather than crashing on a raw transport exception.

**Why this priority**: Gallery tools run inside conversations; opaque exceptions are expensive to diagnose. This story is independently testable and does not change the happy path from P1.

**Independent Test**: Can be fully tested by invoking the request operation with missing config, invalid method/path, mocked non-success HTTP, mocked transport failure, and mocked non-JSON success bodies, asserting a distinct typed error in each case and that no outbound request is sent for config/validation failures.

**Acceptance Scenarios**:

1. **Given** no project auth token, **When** the integration is constructed, **Then** a configuration error is raised and no outbound request is sent.
2. **Given** no Retail base URL in project, credentials, globals, or environment, **When** the integration is constructed with a valid auth token, **Then** it uses the hardcoded staging Retail host.
3. **Given** an HTTP method other than GET, POST, PUT, or PATCH (including DELETE), **When** the developer calls request, **Then** a validation error is raised before any outbound request is sent.
4. **Given** a missing path/endpoint, an empty path, or an absolute `http(s)://` URL, **When** the developer calls request, **Then** a validation error is raised before any outbound request is sent.
5. **Given** Retail responds with a non-success status, **When** the request completes, **Then** an HTTP error exposing status code and response body is raised.
6. **Given** the request fails before a response is received, **When** the operation completes, **Then** a network error is raised.
7. **Given** a success response whose body is not valid JSON (or is not an object/array), **When** the operation completes, **Then** a response error is raised rather than returning a misleading value.

---

### User Story 3 - Use the integration from a Tool with the same ergonomics as contacts (Priority: P3)

A toolkit developer authoring a `Tool` wants a small, discoverable VTEX API that mirrors contacts: a facade bound to the tool (`self.vtex`), a shorthand (`self.gallery_vtex`), a dedicated sender that owns proxy semantics, and a client that owns URL, auth, and error translation. They should not import or construct the client inside `execute`. Successful calls are recorded in the tool operation log without leaking secrets that may live in headers or bodies.

**Why this priority**: Consistency with contacts/broadcasts is how developers find the feature; it depends on P1 and P2 being available through the facade.

**Independent Test**: Can be fully tested by constructing a tool with a valid execution context, calling `self.vtex.request` and `self.gallery_vtex`, verifying both delegate to the same sender, and verifying the operation log records path and method only after success.

**Acceptance Scenarios**:

1. **Given** a tool instance with a configured execution context, **When** the developer accesses `self.vtex`, **Then** they can call `request` without manual client setup.
2. **Given** the same tool instance, **When** the developer calls `self.gallery_vtex(...)`, **Then** it is equivalent to `self.vtex.request(...)`.
3. **Given** a successful request, **When** the operation completes, **Then** the tool operation log contains a `vtex_requests` entry with path and method only (no headers or body).
4. **Given** a request that fails validation or transport, **When** the operation raises, **Then** the operation log is not updated for that call.
5. **Given** the VTEX package is imported from the toolkit public surface, **When** a developer reads the package exports, **Then** the facade, sender, client, and error types are available together.

---

### Edge Cases

- What happens when both `path` and `endpoint` are supplied? `path` takes precedence.
- What happens when neither `path` nor `endpoint` is supplied? A validation error is raised before any outbound request.
- What happens when the method is lowercase (`get`)? It is uppercased and accepted if it is one of GET/POST/PUT/PATCH.
- What happens when optional headers/params/merchant_name are empty or omitted? They are omitted from the proxy payload rather than sent as empty objects/strings.
- What happens when `data` is an empty dict or empty list? It is still forwarded because it is an explicit body (`data is not None`).
- What happens when Retail returns HTTP 204 with an empty body? The caller receives a response error rather than `None`, because VTEX proxy callers expect a JSON object or array.
- What happens when the auth token is present but `retail_url` is absent from context and environment? Construction succeeds using the hardcoded staging default.
- What happens when the auth token is present but `retail_url` is only in the environment? Construction succeeds using `RETAIL_BASE_URL`.
- What happens when the Retail URL has a trailing slash? The trailing slash is stripped before joining the proxy path.
- What happens when headers contain VTEX app keys or tokens? They are forwarded to Retail as VTEX headers, but they MUST NOT appear in the tool operation log.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The toolkit MUST expose a new `vtex` domain package with a public API structured analogously to the existing `contacts` package (facade + sender + typed errors + colocated tests).
- **FR-002**: The VTEX sender MUST perform all Retail HTTP communication through a Retail client in the same package; it MUST NOT duplicate URL joining, Bearer header construction, or transport-error translation.
- **FR-003**: The integration MUST resolve the Retail base URL with precedence `project.retail_url` → `credentials.retail_url` → `globals.retail_url` → environment `RETAIL_BASE_URL` → hardcoded staging default `https://retailsetup.stg.cloud.weni.ai`.
- **FR-004**: The integration MUST authenticate to Retail using `context.project.auth_token` as a Bearer token. Missing token MUST raise a configuration error at construction. The integration MUST NOT introduce a new token key in v1.
- **FR-005**: The request operation MUST post to Retail's generic VTEX proxy path `/vtex/proxy/` with a JSON body containing `method` (uppercase) and `path` (normalized with a leading `/`).
- **FR-006**: The request operation MUST accept `path` or `endpoint` (alias). When both are provided, `path` wins. When neither is provided, a validation error MUST be raised before any outbound request.
- **FR-007**: Allowed methods are GET, POST, PUT, and PATCH (case-insensitive). Any other method, including DELETE, MUST raise a validation error before any outbound request.
- **FR-008**: Absolute `http://` or `https://` paths MUST be rejected with a validation error. Empty or whitespace-only paths MUST also be rejected.
- **FR-009**: Optional `headers`, `data`, `params`, and `merchant_name` MUST be included in the proxy body only when provided (`headers`/`params`/`merchant_name` when truthy; `data` when not `None`).
- **FR-010**: A successful proxy response MUST return the parsed JSON object or array. A success body that is empty or not JSON MUST raise a response error.
- **FR-011**: Transport failures MUST be translated into VTEX-specific errors with a common base type: configuration, validation, HTTP (status code + body), network, and unreadable success body.
- **FR-012**: The Tool facade MUST be registered as `vtex` so developers can call `self.vtex.request(...)`. The facade MUST also expose the shorthand `self.gallery_vtex` mapped to `request`. `Tool` itself MUST NOT gain hard-coded VTEX methods.
- **FR-013**: After a successful request, the facade MUST append `{path, method}` to the tool operation log under `vtex_requests`. Headers and body MUST NOT be logged. Failures MUST NOT append an entry.
- **FR-014**: Existing broadcasts and contacts behavior MUST remain unchanged.
- **FR-015**: User-visible API changes MUST be documented in the project changelog and a user-guide page when the public surface is exported.
- **FR-016**: Payment-gateway and payment-transaction proxies MUST NOT be part of this feature.

### Key Entities

- **VTEX Request**: A developer-facing call identified by a VTEX path and HTTP method, with optional headers, body, query parameters, and merchant name.
- **Retail VTEX Proxy**: The existing Retail endpoint that resolves the project's VTEX account, signs inter-module credentials, and forwards the call to VTEX IO. The toolkit treats it as the only outbound hop.
- **Execution Context**: The runtime object attached to a tool execution that supplies `project.auth_token` and optionally `retail_url`.
- **VTEX Facade**: The developer-facing entry point bound to a tool (`self.vtex` / `self.gallery_vtex`).
- **VTEX Sender**: The component that validates method/path and builds the proxy payload.
- **Retail Client**: The component that resolves Retail URL and token, issues the POST, and translates transport failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A toolkit developer can call a VTEX private API in a single operation without writing custom HTTP, URL, or authentication code.
- **SC-002**: The namespaced call and the `gallery_vtex` shorthand are interchangeable for the same arguments.
- **SC-003**: 100% of VTEX integration tests pass with no real network calls, and total toolkit test coverage remains at or above the project minimum (95%) after the feature merges.
- **SC-004**: Configuration and validation failures never send an outbound request (verified in automated tests).
- **SC-005**: Failure modes (missing token, invalid method, invalid path, HTTP error, network error, unreadable body) each produce a distinct, actionable error message verifiable in automated tests.
- **SC-006**: A developer familiar with the contacts package can locate equivalent facade, sender, client, and error types in the VTEX package within one minute of browsing the repository structure.
- **SC-007**: The operation log for a successful call contains path and method and does not contain headers or body data.

## Assumptions

- Retail's generic VTEX proxy (`POST /vtex/proxy/`) already exists, authenticates with the same project-scoped JWT currently injected as `context.project.auth_token` by Retail's ActiveAgent invoke, and forwards method/path/headers/data/params/merchant_name to VTEX IO.
- The execution runtime may supply `retail_url` on the project (preferred) or via `RETAIL_BASE_URL`. When neither is set, the client uses the staging host `https://retailsetup.stg.cloud.weni.ai` until it is replaced with production after tests.
- Reusing `auth_token` means a single tool execution that must talk to both Flows and Retail depends on the runtime putting a token both services accept, or on the developer not mixing the two integrations in one run. That trade-off is accepted for v1.
- DELETE is out of scope because the Retail proxy serializer does not accept it.
- Path allowlisting, JWT signing for VTEX IO, account-domain resolution, and merchant seller checks remain Retail's responsibility.
- Public API names and documentation remain in English to match existing toolkit conventions.

## Dependencies

- Existing Retail VTEX proxy endpoint — external dependency operated by Retail.
- Existing Tool integration registry (`Tool.register_integration` and `_tool_methods`) — no changes to `Tool` internals required.
- Contacts and broadcasts packages — structural references only; no code changes required in those packages.

## Out of Scope

- Payment gateway proxy (`/vtex/payments/gateway-proxy/`) and payment transaction proxy (`/vtex/payments/send-transaction/`).
- Calling VTEX IO directly from the toolkit (signing `X-Weni-Auth`, resolving `*.myvtex.com`, workspace prefixes).
- Introducing a separate `retail_auth_token` context key.
- Hardcoding a default Retail production or staging host.
- Changes to Retail's proxy views, serializers, or JWT generation.
- Path allowlists or VTEX credential management inside the toolkit.
