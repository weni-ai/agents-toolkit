# Feature Specification: Flows Contacts Integration

**Feature Branch**: `002-flows-contacts`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "preciso criar uma nova integração do Flows ao toolkit, parecido com a forma que criamos a integração com a endpoint de broadcasts weni/broadcasts/broadcast.py, agora precisamos criar para a endpoint de contact, mais especificamente, precisamos conseguir dar um get unico no contact urn do usuario da conversa e um update nesse contact usando sua urn, essa é a endpoint contacts do flows /Users/marcell/flows/temba/api/v2/views.py:L1874-L2185 , sua url é /api/v2/contacts, aqui vai um exemplo de curl: curl --location 'https://flows.weni.ai/api/v2/contacts.json?urn=whatsapp%3A5582999893640' --header 'Authorization: ' --header 'Content-Type: application/json' --data-raw '{ \"fields\": { \"email\": \"leonardo.amaral@vtex.com\" } }'. utilize a abstração do cliente do flows que fizemos agents-toolkit/weni/flows no sender dessa nova integração, crie uma pasta chamada contacts e baseis a estrutura geral como a de agents-toolkit/weni/broadcasts."

## Clarifications

### Session 2026-06-11

- Q: No escopo v1, a operação de update deve aceitar apenas custom fields ou também outros atributos suportados pelo endpoint Flows? → A: Full write surface — update aceita qualquer atributo suportado pelo endpoint Flows (incl. `name`, `language`, `groups`, `fields`, `urns`).
- Q: Quando o URN não existe no Flows, o update deve criar o contato ou falhar? → A: Update-only — falha com erro not-found se o contato não existir; a integração não deve criar contatos implicitamente via update.
- Q: A integração deve tentar URN alternativo (9º dígito) quando o get inicial não encontrar contato WhatsApp Brasil? → A: 9th-digit retry — se not-found e URN for `whatsapp:55...`, tenta variante com/sem o 9º dígito antes de falhar; operações subsequentes (update) usam o URN que efetivamente encontrou o contato.
- Q: Se o payload incluir `urns` no body enquanto o contato é identificado por URN na query, rejeitar ou omitir? → A: Reject — falha com erro de validação antes de chamar Flows.
- Q: Como a operação de update deve receber os atributos (dict vs kwargs)? → A: Hybrid — aceita dict ou kwargs; em conflito, kwargs têm precedência sobre chaves do dict.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retrieve the current conversation contact from Flows (Priority: P1)

A toolkit developer building a conversational agent needs to read the Flows contact record for the person currently in the conversation. During tool execution, the contact's URN is already available from the execution context (for example, a WhatsApp URN). The developer invokes a contacts operation that resolves that URN automatically and returns the matching contact data from Flows — including identity fields, custom fields, groups, and status flags — without manually building authenticated requests or parsing list responses.

**Why this priority**: Reading contact data is the foundation for personalization, validation, and conditional logic inside tools. Without a reliable single-contact lookup, downstream update flows cannot safely decide what to change.

**Independent Test**: Can be fully tested by providing an execution context with a contact URN, invoking the get-by-URN operation (with the Flows platform mocked), and verifying that exactly one contact record is returned with the expected attributes when Flows has a match.

**Acceptance Scenarios**:

1. **Given** an execution context whose contact includes a primary URN, **When** the developer requests the contact by that URN, **Then** the integration returns the single matching contact record from Flows.
2. **Given** a contact URN present in multiple context locations (contact object and parameters), **When** the integration resolves the URN, **Then** it uses the same precedence rules as existing Flows integrations so behavior is predictable across features.
3. **Given** Flows returns a paginated list wrapper containing one result for the filtered URN, **When** the get operation completes, **Then** the developer receives the contact object itself, not the raw list envelope.
4. **Given** no contact URN can be resolved from the execution context, **When** the developer attempts a get, **Then** a clear configuration error is raised before any outbound request is sent.
5. **Given** a WhatsApp Brazil URN (`whatsapp:55...`) that does not match on the first lookup, **When** an alternate 9th-digit variant exists in Flows, **Then** the get operation returns the contact found via that variant and uses the matching URN for subsequent update operations.

---

### User Story 2 - Update contact attributes on the conversation contact (Priority: P2)

A toolkit developer needs to persist data collected during a conversation — such as an email address, name, language, group membership, or other contact attributes — back to the contact record in Flows. They provide the attributes to update and the integration sends an authenticated update for the contact identified by the conversation URN. Only the supplied attributes are changed; other contact data remains untouched.

**Why this priority**: Updating contact attributes closes the loop between conversational agents and the CRM/contact store, enabling agents to enrich profiles during interactions.

**Independent Test**: Can be fully tested by providing an execution context with a contact URN and a payload of supported write attributes (for example, `fields`, `name`, or `language`), invoking the update operation (with Flows mocked), and verifying the outbound update targets the correct URN and payload shape.

**Acceptance Scenarios**:

1. **Given** an execution context with a resolvable contact URN and a payload of supported write attributes (for example, `fields`, `name`, `language`, or `groups`), **When** the developer updates the contact, **Then** Flows receives an update scoped to that URN with only the provided attributes in the payload.
2. **Given** a successful update response from Flows, **When** the operation completes, **Then** the developer receives the updated contact representation returned by Flows.
3. **Given** an explicit URN override is supplied for the update, **When** the developer updates the contact, **Then** that URN is used instead of the context-derived URN.
4. **Given** Flows responds with a non-success status for the update, **When** the operation completes, **Then** the developer receives a contacts-specific error with enough detail to diagnose the failure.
5. **Given** no contact exists in Flows for the resolved URN, **When** the developer attempts an update, **Then** the integration fails with a not-found error before or without creating a new contact record.
6. **Given** an update invoked with both a payload dict and keyword arguments for the same attribute, **When** the integration builds the request body, **Then** keyword arguments override conflicting keys from the dict.
7. **Given** an update payload that includes `urns` while the contact is identified by URN in the query string, **When** the developer attempts the update, **Then** a validation error is raised before any outbound request is sent.

---

### User Story 3 - Use the integration from tool execution with the same ergonomics as broadcasts (Priority: P3)

A toolkit developer authoring a `Tool` wants a small, discoverable contacts API that mirrors the broadcasts pattern: a facade object bound to the tool, backed by a dedicated sender component that delegates HTTP concerns to the shared Flows client abstraction. They should not reimplement authentication, base URL resolution, or error translation for each new contacts use case.

**Why this priority**: Consistency reduces learning cost and prevents divergence between Flows integrations; it depends on P1 and P2 being available through the sender.

**Independent Test**: Can be fully tested by constructing a tool with a valid execution context, calling the public contacts facade methods, and verifying they delegate to the sender which in turn uses the shared Flows client (all external calls mocked).

**Acceptance Scenarios**:

1. **Given** a tool instance with a configured execution context, **When** the developer accesses the contacts facade, **Then** they can call get and update operations without manual client setup.
2. **Given** the shared Flows client raises a typed platform error, **When** a contacts operation fails, **Then** the failure is surfaced through contacts-specific error types consistent with other toolkit domain packages.
3. **Given** the new contacts package is imported from the toolkit public surface, **When** a developer reads the package exports, **Then** the primary facade, sender, and error types are available alongside one another following the broadcasts package layout.

---

### Edge Cases

- What happens when Flows returns an empty result set for the requested URN? The get operation must fail with a clear not-found style error rather than returning empty or ambiguous data.
- What happens when Flows returns more than one result for a URN filter (unexpected duplicate)? The get operation must fail with an explicit ambiguity error rather than silently picking one record.
- What happens when a WhatsApp Brazil URN (`whatsapp:55...`) is not found with the exact digits from context? The integration must retry lookup using the alternate 9th-digit variant before raising not-found; if the alternate matches, that URN becomes the effective identifier for the rest of the operation (including update pre-check and write).
- What happens when the update payload is empty or contains no supported write attributes? The integration must reject the call before sending a meaningless request.
- What happens when the caller includes `urns` in the update body while also identifying the contact by URN in the query string? The integration must reject the call with a validation error before contacting Flows; it must not silently strip or override the query URN.
- What happens when the contact URN requires URL encoding (for example, `whatsapp:5582999893640`)? The integration must transmit the URN correctly in query parameters.
- What happens when Flows would create a new contact because the URN did not exist (platform default on POST-by-URN)? The integration MUST NOT allow implicit creation: it verifies the contact exists (via get-by-URN) before sending the update, and fails with a not-found error if no matching contact is found.
- What happens when the auth token is missing from the execution context? The shared Flows client configuration error is raised before any contacts request is attempted.
- What happens when the network fails before a response is received? The developer receives a contacts-specific error distinguishable from configuration and HTTP response failures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The toolkit MUST expose a new `contacts` domain package with a public API structured analogously to the existing `broadcasts` package (facade + sender + typed errors + colocated tests).
- **FR-002**: The contacts sender MUST perform all Flows HTTP communication through the shared Flows client abstraction; it MUST NOT duplicate manual request plumbing already centralized in that client.
- **FR-003**: The integration MUST resolve the conversation contact URN from the execution context using the same precedence as existing Flows integrations: `contact.urns[0]`, then `contact.urn`, then `parameters.contact_urn`.
- **FR-004**: The integration MUST support retrieving a single contact by URN against the Flows contacts endpoint (`/api/v2/contacts.json`) filtered by the `urn` query parameter.
- **FR-005**: When retrieving by URN, the integration MUST return exactly one contact object; if zero matches are found (after any applicable URN retry), it MUST raise a not-found error; if more than one match is found, it MUST raise an ambiguity error.
- **FR-005a**: For WhatsApp Brazil URNs (`whatsapp:55...`), when a get-by-URN returns no match, the integration MUST retry with the alternate 9th-digit variant before raising not-found. When a match is found via the alternate URN, that URN MUST be used as the effective identifier for subsequent operations in the same call chain (including update pre-check and write).
- **FR-006**: The integration MUST support updating an **existing** contact by URN via an authenticated write to the contacts endpoint with the URN supplied as a query parameter and a body containing the attributes to change. The integration MUST NOT create new contacts as a side effect of update.
- **FR-006a**: Before sending an update, the integration MUST verify the contact exists for the target URN (for example, via the get-by-URN operation). If no contact is found, it MUST raise a not-found error and MUST NOT issue the update request.
- **FR-007**: The update operation MUST accept any write attribute supported by the Flows contacts endpoint (`name`, `language`, `urns`, `groups`, `fields`, and future-compatible keys). It MUST support both a payload dict and keyword arguments; when the same attribute is supplied in both, keyword arguments MUST take precedence. Only the merged, provided attributes MUST be sent in the request body. When the contact is identified by URN in the query string, the integration MUST reject the request with a validation error if `urns` is present in the merged body, per Flows platform constraints.
- **FR-008**: Both get and update operations MUST allow an optional explicit URN argument that overrides the context-derived URN.
- **FR-009**: The integration MUST translate Flows client failures into contacts-specific error types with a common base error, mirroring the broadcasts sender error pattern.
- **FR-010**: The integration MUST include automated tests with mocked external calls covering URN resolution, successful get/update flows, empty-result handling, 9th-digit URN retry, hybrid update payload merging (dict + kwargs precedence), `urns`-in-body validation rejection, HTTP failures, and configuration errors.
- **FR-011**: The integration MUST preserve existing broadcasts behavior; no breaking changes to the broadcasts package are permitted in this feature.
- **FR-012**: User-visible API changes MUST be documented in the project changelog when the public surface is exported.

### Key Entities

- **Contact**: A person served by the conversational agent in Flows; identified by one or more URNs and carrying attributes such as name, language, custom fields, group memberships, blocked/stopped flags, and timestamps.
- **Contact URN**: The canonical identifier used to locate a contact in Flows for the current conversation (for example, a WhatsApp-scheme URN).
- **Contact Fields**: A key-value map of custom attributes stored on a contact (for example, `email`), used as the primary update payload in the initial scope.
- **Execution Context**: The runtime object attached to a tool execution that supplies project credentials, contact identity, and parameters used to configure Flows integrations.
- **Contacts Facade**: The developer-facing entry point bound to a tool, exposing get and update operations for the conversation contact.
- **Contacts Sender**: The component that builds contacts-specific requests (path, query parameters, body) and delegates transport to the shared Flows client.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A toolkit developer can retrieve the conversation contact record in a single call without writing custom HTTP or authentication code.
- **SC-002**: A toolkit developer can update any supported contact write attribute (for example, a custom field such as email, or top-level attributes such as name or language) by URN in a single call, with the change reflected in the Flows response payload.
- **SC-003**: 100% of contacts integration tests pass with no real network calls, and total toolkit test coverage remains at or above the project minimum (95%) after the feature merges.
- **SC-004**: Contacts operations reuse the shared Flows client for all outbound requests — zero duplicated base URL, header, or auth resolution logic in the contacts sender.
- **SC-005**: Failure modes (missing URN, contact not found, HTTP error, network error) each produce a distinct, actionable error message verifiable in automated tests.
- **SC-006**: A developer familiar with the broadcasts package can locate equivalent facade, sender, and error types in the contacts package within one minute of browsing the repository structure.

## Assumptions

- The Flows contacts API POST-by-URN can create a contact when the URN is unknown; this integration deliberately overrides that platform default by enforcing update-only semantics (existence check before write).
- Initial scope is limited to **get single contact by URN** and **update contact by URN**; listing all contacts, creating contacts without an existing URN context, and deleting contacts are out of scope for this iteration.
- The conversation URN available in the execution context is sufficient for identifying the contact in typical agent flows; UUID-based lookup is not required in v1 but may be added later without breaking URN-based operations.
- The shared Flows client from the completed `001-flows-client` feature is available and is the mandated transport layer for this integration.
- Custom field keys and values follow Flows validation rules; the integration forwards them as-is and surfaces platform validation errors through the standard HTTP error path.
- Portuguese/English mixed input in the feature request reflects team language preference only; public API names and documentation remain in English to match the existing toolkit conventions.

## Dependencies

- Shared Flows client abstraction (`weni.flows`) — completed in feature `001-flows-client`.
- Flows platform contacts endpoint (`/api/v2/contacts.json`) — external dependency operated by the Flows service.
- Existing broadcasts package — structural reference only; no code changes required in broadcasts for this feature.

## Out of Scope

- Refactoring the broadcasts sender to use the shared Flows client (may happen in a separate feature).
- Bulk contact operations, contact search, group management, or contact deletion.
- Changes to the Flows server-side contacts endpoint implementation.
- UI or admin tooling for contact management outside conversational agent tools.
