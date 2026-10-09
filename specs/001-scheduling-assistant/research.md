# Research: scheduling assistant

Reviewed: 2026-10-08. Research is design evidence, not runtime qualification. Source precedence and delivery constraints: [spec](spec.md), [Q1](scope-decisions.md), [product decisions](../../docs/product/decisions.md). Read-only API and UI research were delegated independently; one writer integrates artifacts. No model call, credential access, publication or implementation occurred.

## Core and transport

- Decision: Python 3.11+ package `scheduling_assistant`, dataclasses/enums and standard-library JSON/HTTP adapters; unittest behavior tests. Add Marimo as the sole UI runtime dependency, using reviewed candidate `marimo==0.25.0` (Python >=3.10 metadata), with a local compatibility smoke check during implementation.
- Rationale: existing project requires Python 3.11+, supports unittest and has no application dependencies. An injected interpreter and scheduling gateway keep tests offline while using real HTTP in integration. No SDK, agent framework, database or rule engine is needed for the accepted slice.
- Alternatives considered: separate web backend, ORM, general agent orchestration and new scheduling mock add complexity without accepted outcomes. Generic `poc_demo` is starter evidence only and cannot qualify scheduling.

## Service facts and strict client validation

- Decision: use the supplied independent server and its public [OpenAPI](../../docs/product/RFP/source/openapi/scheduling-api.yaml). Implement four required operations; existing appointment lookup and recorded handoff remain deferred. Runtime never reads fixtures as facts.
- Rationale: [mock guide](../../docs/product/RFP/source/mock-api/README.md) and inspected server implement synthetic identity, providers, availability, booked slots, deterministic conflict and outage. YAML response properties are not required, so the client must validate its necessary fields explicitly. Appointment lacks slotId; compare patientId, providerId, specialty, location, startTime and scheduled status with the stored proposal, plus nonempty appointmentId and HTTP201.
- Alternatives considered: schema-only mocks fail to reproduce supplied behavior; treating all HTTP2xx as success or accepting model-created IDs is unsafe.
- Boundaries: exact phone/DOB matching; private ZIP disambiguation; enum and calendar/date-range validation in client. Server-local relative dates use a fixed -05:00 offset, not DST support. In-memory server has no durable idempotency/authentication and no concurrency correctness guarantee. Client failures remain truthful.

## AI interpretation

- Decision: HTTPS Responses API through a small standard-library adapter, explicit `--model` (qualification target `gpt-5.4-mini`), environment OPENAI_API_KEY, `store:false`, strict structured extraction and no model tools with direct effect authority. Supply current turn and minimal safe workflow context; do not send candidate responses, secrets or stored patient IDs. Extract sensitive answers only when needed from synthetic input, and never log requests/responses.
- Rationale: official [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) supports constrained output and distinct refusal handling. Local validation must still reject incomplete or invalid interpretations. This is our design inference, not proof of semantic accuracy.
- Alternatives considered: unconstrained prose as booking authority, canned regex-only conversation and automatic tool loops do not meet the accepted AI/safety boundary. Deterministic scripted interpreter remains a labeled test double only.
- Evidence: official [Responses guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses) documents `store:false`; it is not a zero-retention or compliance claim. Official [model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) lists structured output support. Neither source verifies this project's account access. Shared availability is developer-reported; both interfaces require actual live qualification later. Reviewed 2026-10-08.

## Consent, failures and unknown writes

- Decision: store an immutable proposal with conversation/patient generation and displayed slot snapshot. Accept only a subsequent standalone affirmative answer to that unchanged displayed proposal; changed fields, ambiguous text, decline or reset invalidate consent. Lock and mark proposal in-flight before one POST; repeat submission cannot duplicate it.
- Rationale: model extraction may suggest intent but cannot establish identity, slot membership or consent. Deterministic response rendering avoids invented scheduling/medical facts.
- Alternatives considered: trusting a model confirmation flag, carrying consent across changed preferences or retrying a timed-out write violates FR-006–008.
- Recovery: 409 invalidates selection, refreshes returned availability and requires new choice/consent. Hide the already rejected slot during that recovery cycle because the supplied permanent trap reappears. Unknown POST outcome retains a process-level unresolved-effect guard even after conversation reset. No automatic reconciliation endpoint exists in the required slice: instruct clinic scheduling staff to verify before another attempt. Restart/process loss does not prove failure; warn and document this durability limitation. No blind retries, including HTTP redirects for POST.

## Thin presentation and assets

- Decision: CLI and Marimo both submit turns to the same session controller. Form/transcript UI uses submitted values, session-local state, processing feedback and a serial effect owner; reactive rendering never executes a booking. Escape user/service text. Bind UI only to 127.0.0.1:28180; supplied service binds 127.0.0.1:4010. Check ports before launch; do not kill unrelated listeners.
- Rationale: approved Q1 makes Marimo required despite the generic optional profile. Official [form](https://docs.marimo.io/api/inputs/form/), [state](https://docs.marimo.io/api/state/) and [CLI](https://docs.marimo.io/cli/) docs support submitted values, historical inputs and host/port controls. Reviewed [release metadata](https://pypi.org/project/marimo/) identifies 0.25.0; installation remains unverified. Native form/state facilities permit a small adapter; reruns and repeated clicks still require core deduplication. Record keyboard/focus/status checks without claiming accessibility conformance.
- Alternatives considered: full SPA and a giant one-shot form add work or fail multi-turn requirements.
- Asset observation: initial inspection found placeholders only. During planning, another local writer supplied `assets/ui/branding/ochsner-health.svg`, `assets/ui/themes/ochsner.css` and an updated [provenance index](../../docs/internal/ui-assets.md). Final inspection confirms those files and the index reports Operator-approved cache adoption for internal review. This stage did not copy or alter those assets or independently inspect the private approval record. Use these local assets, verify safe SVG/CSS content and visible UI references during implementation; no hotlinks or public permission inferred.

## Verification and documentation

- Decision: tests first for safety transitions, adapters, privacy and interface replay; supplied-server success/failure demos; clean-copy installation; separate live AI flows in CLI and UI. Near-final as-built/video work follows stabilized code and integrated verification.
- Rationale: mock/scripted tests prove boundaries, not live model quality or assignment delivery. Persona placeholders remain explicit; US4 support needs are diagnostics/docs, not an admin console.
- Alternatives considered: scaffold demo success, raw transcript traces, duplicate status ledgers and unsupported time-window claims provide misleading evidence.

No unresolved technical design clarification remains. Pending implementation evidence: dependency pin/smoke, approved asset/UI verification, persona validation, live qualification, latency and clean-copy runs. These are explicit work items and limitations, not claims of completion or extra approval gates.
