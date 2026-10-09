# Feature Specification: AI Appointment Scheduling Assistant

**Feature Branch**: None created; Git extension disabled.

**Created**: 2026-10-08

**Status**: Implemented and qualified; approved focused Persona follow-on reconciled 2026-10-09.

**Input**: Include the client requirements indexed by docs/product/RFP/README.md; reconcile background stories and Persona mappings with supplied intake.

## Clarifications

### Session 2026-10-08

- Q: Which approved scope and delivery contract governs the scheduling MVP? → A: Developer-supplied Q1 selects B, the existing approved common contract: assignment, policies and OpenAPI take precedence; appointment lookup is optional/deferred, with phone + DOB and private ZIP protection retained in booking and truthful human assistance for unsupported lookup. Genuine AI multi-turn CLI and thin Marimo form/transcript, independent supplied mock, service-returned slots, current exact patient-bound consent, booked-only success, fresh choice/confirmation after conflict, no blind retry of unknown booking outcomes, no raw sensitive logs, approved local sponsor assets, tests-first verification and near-final as-built/video documentation remain required. Exact ports, environment/model qualification and delivery boundaries are preserved in [approved Q1 delivery constraints](scope-decisions.md); model availability is developer-reported, and MVP live flow qualification remains required. Local authorization adds no remote provisioning authority; MLX owns remote provisioning.

## User Scenarios & Testing *(mandatory)*

Sources: [assignment](../../docs/product/RFP/source/assignment.md), [policies](../../docs/product/RFP/source/policies.md), [scenarios](../../docs/product/RFP/source/scenarios.yaml). Story wording is inferred from specified journeys; origin is separate from scope acceptance. Approved follow-on maps US1–3 to exact pinned Jules and Ellie-Rae hypotheses, US4 to human support Morgan-Rae and agent QA Sam-Rae in [Personas](../../docs/product/personas.md). Synthetic patient names remain fixtures. The selected hypotheses are not real-user validation or permissions; origin and accepted scope remain separate.

### User Story 1 - Find providers (Priority: P1)

As Jules, with Ellie-Rae’s constrained-input lens, I want to ask which providers serve my specialty and location, so I can explore options without giving patient identity information.

**Origin / scope**: INFERRED wording from assignment Required 1–3 and `provider_lookup`; capability explicitly required.

**Why this priority**: Provider discovery is a required intent and delivers value independently of booking.

**Independent Test**: Ask for downtown primary care providers across multiple turns; compare output with the supplied scheduling service's response.

**Acceptance Scenarios**:

1. **Given** a request missing information needed to narrow the search, **When** the assistant asks a follow-up and the user answers, **Then** it retains request context and shows only returned matching providers.
2. **Given** a provider-only request, **When** providers are searched, **Then** patient identification is not required and no patient-specific information is displayed.
3. **Given** empty results or an unsupported request, **When** the search cannot satisfy it, **Then** the assistant explains the limitation and offers a supported next step or human assistance without inventing providers.

### User Story 2 - Confirm and book an appointment (Priority: P1)

As Jules, with Ellie-Rae’s constrained-input lens, I want to identify myself, choose an available appointment and explicitly confirm it, so I control booking and know whether it succeeded.

**Origin / scope**: INFERRED wording from assignment Required 1, 2, 4, policies and `happy_path_booking`; explicitly required.

**Why this priority**: This is the required consequential end-to-end journey.

**Independent Test**: Use the supplied unique-match synthetic patient and downtown primary care availability; observe one confirmed booking and returned appointment.

**Acceptance Scenarios**:

1. **Given** a booking request missing identity information, **When** the assistant gathers phone and date of birth, **Then** it resolves identity through the supplied service before patient-specific availability or booking.
2. **Given** a unique patient match and supported preferences, **When** availability is retrieved, **Then** the user sees only returned available slots with provider reference, specialty, location and date/time including the supplied offset.
3. **Given** selection of a displayed slot, **When** the assistant presents the exact proposal, **Then** it asks explicit confirmation; only a subsequent affirmative response authorizes that proposal.
4. **Given** a confirmed proposal, **When** booking succeeds, **Then** the assistant reports the returned appointment identifier and details without inventing confirmation.
5. **Given** a pending proposal, **When** the user declines, changes patient/slot or gives an ambiguous reply, **Then** no booking occurs; a changed proposal requires fresh confirmation.
6. **Given** a completed proposal in the current conversation, **When** confirmation repeats, **Then** the known result is shown without another booking. Cross-session replay protection is not promised.

### User Story 3 - Resolve identity safely and obtain help (Priority: P1)

As Jules, with Ellie-Rae’s constrained-input lens, I want a specific explanation and safe next step when scheduling cannot proceed, so I do not see another patient's details or mistake failure for success.

**Origin / scope**: INFERRED wording from assignment Required 5, policies, `no_patient_match`, `multiple_patient_matches` and recommended failure scenarios. No-match is the selected required demonstration failure; policy safety applies to every reachable failure independently of optional harness scope.

**Why this priority**: Safety is necessary for the required booking journey.

**Independent Test**: Use no-match and duplicate-match inputs, an advice request and an outage; inspect user output and absence of unsafe actions.

**Acceptance Scenarios**:

1. **Given** no patient match, **When** correction still cannot resolve identity, **Then** the assistant stops patient-specific actions and gives a truthful human-assistance next step without revealing patient data or guessing identity.
2. **Given** multiple matches, **When** the assistant asks for ZIP code, **Then** it compares the answer against returned candidates without revealing their demographic details; exactly one match permits proceeding, otherwise it hands off.
3. **Given** a request for medical advice, a human or an unsupported specialty, location, appointment type or operation, **When** recognized, **Then** the assistant stops the unsupported workflow, gives no medical advice or triage and explains a human-assistance next step.
4. **Given** no available slots, **When** results return, **Then** it explains that none are available and offers a changed supported search or human assistance.
5. **Given** a displayed slot becomes unavailable, **When** booking is rejected, **Then** it says the slot was taken and offers refreshed alternatives or human assistance; a new slot requires fresh choice and confirmation, and it never reports successful booking.
6. **Given** service unavailability or an unknown action outcome, **When** failure occurs, **Then** it gives a specific explanation, avoids unbounded retries and distinguishes failure from uncertainty; an unknown booking outcome cannot be blindly retried or cleared by reset. It never claims a handoff was queued without a successful receipt.

### User Story 4 - Inspect safe recovery context (Priority: P2)

As Morgan-Rae, the human Support/Admin hypothesis, I want accurate diagnostics and recovery context, so I can understand failures without exposing sensitive identifiers or making the user repeat work.

**Origin / scope**: INFERRED background support seed reconciled with policy Observability and assignment documentation. Diagnostic coverage is required by policy; no admin console or delivery permission is inferred.

**Why this priority**: Support and reviewers need observable boundaries and honest outcomes.

**Independent Test**: Inspect diagnostics and recovery documentation for a success and failure without requiring an admin interface.

**Acceptance Scenarios**:

1. **Given** an interaction, **When** diagnostics are inspected, **Then** intent or workflow state, service operations, outcomes/errors, escalation reason and measured latency are distinguishable, with no plaintext phone, full birth date, secrets or other sensitive identifiers.
2. **Given** an unresolved operation, **When** recovery instructions are read, **Then** attempted, completed and unknown outcomes are distinguished and the next step avoids blindly repeating a consequential action.

### User Story 5 - Look up existing appointments (Priority: P2, optional deferred)

As Jules, with Ellie-Rae’s constrained-input lens, I want to verify my identity and see my existing appointments, so I understand my scheduled care.

**Origin / scope**: INFERRED wording from assignment Good-to-have and `multiple_patient_matches`. Developer Q1 selects the approved common contract: assignment, policies and public service contract take precedence; existing appointment lookup is optional and deferred from the MVP. The duplicate-match protection is retained within required booking (US3.2).

**Why this priority**: Useful follow-on patient journey; unsupported lookup must still receive truthful assistance in the MVP.

**Independent Test**: In the MVP, request lookup and verify truthful unsupported-scope guidance. If later selected, use the supplied pre-existing appointments and duplicate patient matches.

**Acceptance Scenarios** (1–2 are conditional follow-on acceptance; 3 is required MVP behavior):

1. **Given** a unique verified patient, **When** existing appointments are requested, **Then** only that patient's returned appointments are shown, or an accurate empty result is stated.
2. **Given** multiple matches, **When** lookup is requested, **Then** ZIP clarification precedes appointment disclosure; unresolved identity leads to human assistance.
3. **Given** lookup is deferred in the MVP, **When** requested, **Then** the assistant explains that it is unsupported and offers human assistance without claiming retrieval.

### Edge Cases

- Missing/malformed identifiers prompt useful bounded clarification, never a guessed patient. ZIP matching zero or multiple candidates never permits patient-specific actions.
- Instructions to skip identity, invent availability or auto-confirm cannot bypass booking rules.
- Undisplayed slot selection, stale confirmation or changed preferences require a fresh valid proposal.
- Repeat confirmation after known success cannot repeat booking within that conversation; uncertain effects require reconciliation before retry.
- Provider discovery may transition to booking but does not establish identity.
- Empty results, invalid requests, malformed responses, outages and interruptions cannot become fabricated success or endless retry/handoff loops.
- Fixture-relative dates and conflict flags are not user-visible scheduling facts; display service-returned time and offset without claiming daylight-saving support.
- Reset clears conversation/identity/confirmation context; restarting the mock resets its bookings. Reset does not prove that an uncertain previous operation failed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The assistant MUST support text-based AI-assisted multi-turn interaction, recognize provider lookup and booking, retain relevant answers during a conversation and ask for missing identity/preferences/slot choice. Disclose AI interaction. Acceptance: US1.1, US2.1–3.
- **FR-002**: Provider lookup MUST use the supplied scheduling service, show only returned providers and require no identity information for provider-only requests. Acceptance: US1.1–3.
- **FR-003**: Before patient-specific availability, booking or appointment disclosure, the assistant MUST resolve patient identity through the supplied service using required identifying information; no guessed or user-selected patient identifier may substitute. Acceptance: US2.1, US3.1–2, US5 if selected.
- **FR-004**: Zero matches MUST prompt correction or human assistance; multiple matches MUST prompt ZIP clarification before proceeding, with unresolved ambiguity terminating patient-specific actions. Candidate demographics MUST NOT be disclosed. Acceptance: US3.1–2.
- **FR-005**: Availability MUST come from the supplied service; only returned available slots may be displayed and selected. Acceptance: US2.2–3 and undisplayed-slot edge case.
- **FR-006**: The current exact booking proposal, bound to the uniquely resolved patient and selected displayed slot, MUST receive explicit user confirmation before execution. Decline, ambiguous input or a changed proposal MUST NOT authorize booking. Acceptance: US2.3, US2.5.
- **FR-007**: Confirmed booking MUST use the supplied service; success MUST be reported only from the contract-defined successful booking response containing a valid returned appointment with status `scheduled`, matching the confirmed patient and slot details; malformed or mismatched results cannot establish success. Repeated confirmation MUST NOT replay a completed proposal in the current conversation. Acceptance: US2.4, US2.6; exact response contract in [Q1 delivery constraints](scope-decisions.md).
- **FR-008**: No availability, slot conflicts, service outages and unknown outcomes MUST receive truthful, specific explanations and supported recovery/human-assistance next steps, with no fabricated data or automatic replay of uncertain bookings. Acceptance: US3.4–6.
- **FR-009**: The assistant MUST provide no medical advice or triage and MUST offer human assistance for advice/human requests, unsupported scope and unresolved identity. Acceptance: US3.1–3.
- **FR-010**: Baseline human assistance MUST explain why work stopped and a practical next step, such as contacting clinic scheduling staff; it MUST NOT invent contact details, staff engagement, a delivered handoff or queued request. Service-recorded handoff is optional; if added, queued status requires a returned receipt. Acceptance: US3.3–6.
- **FR-011**: Diagnostics MUST include intent or workflow state, service operations, outcomes, errors, escalation reason when applicable and basic measured latency, excluding secrets and plaintext sensitive identifiers. Raw sensitive transcripts, identifying parameters and patient responses MUST NOT be logged. Acceptance: US4.1.
- **FR-012**: Documentation MUST explain setup, starting the supplied mock, running the assistant, exact verification commands, success/failure demos and reset, with links to architecture, decisions, assumptions, tradeoffs, limitations and next steps. A repeatable at-most-five-minute walkthrough script MUST cover provider lookup, confirmed booking, one failure and design tradeoffs. Acceptance: reviewer completes documented flows from a clean checkout or explicitly labeled clean-copy equivalent without undocumented steps.
- **FR-013**: Verification MUST cover provider lookup, booking and no-match failure plus refusal, ambiguous identity, privacy and applicable recovery boundaries. Meaningful behavior tests precede implementation. Success/failure demos MUST use the supplied local mock; fixture-only results cannot substantiate integration. Acceptance: expected outcomes and independently inspectable actual service interactions.
- **FR-014**: Existing appointment lookup is optional and deferred from the MVP under developer Q1. Unsupported lookup MUST offer an actual human-assistance next step without claiming retrieval or human engagement. If later selected, identity checks precede disclosure and only returned appointments are shown. Duplicate-match protection remains mandatory in booking. Acceptance: US5.3 for MVP; US5.1–2 only if later selected, and US3.2 for booking.
- **FR-015**: The prototype MUST use synthetic data, exclude credentials from source/diagnostics and describe identity matching as prototype verification rather than production authentication/compliance. Acceptance: boundary documentation and sanitized artifacts inspected; demonstrations use synthetic patients.
- **FR-016**: The MVP MUST provide genuine AI multi-turn conversation through a terminal interface and a local form/transcript interface. Both MUST apply the same identity, service-fact, consent and recovery rules; a canned demonstration or single form submission cannot substitute for live multi-turn qualification. Acceptance: provider lookup, booking and no-match journeys in both interfaces, including follow-ups and refusal before confirmation.
- **FR-017**: The local visual interface MUST use the approved sponsor theme and logo from permitted local assets, with a concise source/use index. Acceptance: visible theme/logo, working asset references, and retained AI disclosure and clear booking controls.

### Key Entities *(include if feature involves data)*

- **Conversation**: Intent, answers/preferences, identity state, displayed options, pending proposal and known outcomes; no cross-session continuity promised.
- **Patient candidate**: Returned synthetic identity with phone, birth date and ZIP used to resolve a unique match; matching is not production authentication.
- **Provider**: Returned reference/name, specialty, locations and modalities; provider discovery does not establish slot availability.
- **Available slot**: Returned reference, provider, specialty, location, start time/offset and availability; it can become unavailable before booking.
- **Booking proposal**: Exact resolved patient and displayed slot awaiting confirmation; changes invalidate prior confirmation.
- **Appointment**: Returned reference, patient/provider relationships, specialty, location, start time and status; cannot be invented.
- **Recovery context**: Reason, sanitized summary, outcome certainty and next step. Optional handoff receipt indicates queued status, not proof of human delivery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the supplied provider journey, 100% of displayed providers originate in the matching service response, with zero identity questions for provider-only requests.
- **SC-002**: One complete synthetic booking journey supports at least two user turns, displays returned availability, obtains explicit confirmation and produces exactly one returned appointment for the chosen slot.
- **SC-003**: All absent, declined, ambiguous and stale confirmation verification cases produce zero booking operations; repeated confirmation after known success produces zero additional bookings in the current conversation.
- **SC-004**: The no-match demo reveals zero patient-specific details, performs zero bookings and ends with a reason-specific human-assistance next step. Duplicate-match cases proceed only after exactly one candidate remains.
- **SC-005**: Every tested advice, unsupported, outage, empty-availability and conflict case gives a truthful limitation/next step, with zero fabricated appointments or unsupported claims of delivered human help.
- **SC-006**: A reviewer identifies intent/state, operation outcome, escalation reason when applicable and elapsed time in success/failure diagnostics, finding zero secrets or plaintext sensitive identifiers.
- **SC-007**: A reviewer following documented clean-project steps completes provider lookup, booking and no-match demonstration without undocumented setup. The walkthrough covers these three flows and architecture/tradeoffs in five minutes or less.
- **SC-008**: Interactive feedback targets 400 ms where feasible; observations record scenario, environment, load and measurement, with unmet targets and longer completion reported honestly. No runtime-performance or user-research success is claimed before measurement.
- **SC-009**: Both user interfaces complete the provider, booking and no-match journeys with retained answers across at least two turns; each produces the same policy-safe outcome, with zero bookings before current explicit consent. Live AI qualification evidence is labeled separately from simulated tests.

## Assumptions

- All 11 manifest text entries were reviewed: assignment, policies, scenarios, public service contract, mock README/source and data README/four fixtures. The only attachment is `.DS_Store`, identified as Apple desktop metadata; its binary contents were not interpreted as requirements. No product conversion is needed based on that classification.
- The client assignment is feature input. Generic starter statements and the unrelated reference text-normalization qualification example are not scheduling requirements or completed implementation evidence. Generic exact-confirmation, finite-recovery and synthetic-boundary decisions remain applicable constraints.
- Baseline: multi-turn provider discovery and confirmed booking, no-match demonstration, policy safety and observability. Optional: service-recorded handoff, broader 3–5-scenario harness, structured/per-step traces, additional visual polish beyond the approved local form/transcript and production/reschedule/cancel design notes. Existing appointment lookup is optional/deferred; the approved terminal and local form/transcript interfaces are required. Rescheduling and cancellation operations are explicitly not required.
- Developer Q1 explicitly resolves source precedence in favor of assignment, policies and public service contract over conflicting scenario priority labels. Duplicate-match identity protection remains required within booking. The scenario requesting a recorded handoff during an outage does not override optional handoff scope or justify a false queued claim when the service cannot accept it. Recommended scenarios provide reproducible safety cases; they do not authorize optional integrations.
- The supplied local scheduling service/public contract is authoritative. Runtime facts must come from it, not direct fixture inspection. Fixtures have relative dates, a hidden conflict marker and fixed time offset; mock state is in memory, without production durability/security guarantees. Implementation-specific operation mapping belongs in the plan.
- No new-patient registration, clinical advice, real patient data, real scheduling system, authenticated admin console or production deployment is included. Unsupported appointment types lead to human assistance.
- Exact primary-user and Support/Admin Persona pins are selected; actual user validation remains pending and no demographic constraints are invented. The support seed is reconciled in US4 and served through diagnostics/documentation without adding a console or permissions.
- AI behavior and live flow qualification remain required for the MVP. Planning must distinguish AI interpretation, service facts and enforced policy, simulated tests and actual live evidence. Exact developer-supplied delivery constraints and model availability qualification are retained in [Q1 scope decisions](scope-decisions.md); availability is a supplied qualification, not verified by Specify. This stage performs no credential access or external model calls.
- The assignment requests a repository link, README and at-most-five-minute video, a three-hour coding window and video due 30 minutes afterward. Operator owns compliance and timing tradeoffs; package receipt time and compliance are unverified. Its requested statement “I completed this within the assigned 3-hour window.” MUST NOT be asserted without evidence. Publication, pushes, video production/submission and deployment are outside this stage's authorization.
- Follow-on implementation must populate actual-code architecture/walkthrough near completion, finalize dated actual-code video notes, maintain a short linked next-step handoff and provide a small teammate modification exercise. These are future project obligations, not work completed by Specify.


## Approved focused Persona follow-on —2026-10-09

Origin: Operator-approved reuse of shared pinned hypotheses, not supplied client research. US1–3 use Jules and Ellie-Rae; US4 uses human Morgan-Rae and agent QA Sam-Rae. [Local pins/cards](../../docs/product/personas.md) preserve exact source ancestry without changing historical bootstrap records. Scope remains original MVP; no console, phone channel, actual transfer or additional service is selected.

- Ellie-Rae: invalid numbered choice retains returned options and matched context; fresh valid selection and separate confirmation remain required. This was verified existing behavior.
- Sam-Rae: failed model interpretation clears pending consent; later yes cannot book until a fresh selection. This was verified existing behavior.
- Morgan-Rae: a request for human help presents local known supported preferences, missing matching field names and actual booking certainty. It never echoes private identity values/candidates, erases unknown/no-retry truth, performs a transfer or claims queued delivery. This drove a tests-first implementation repair. Completed/known-rejected/unknown outcomes remain distinguishable.

118tests, actual suppliedHTTP lost-response support regression, fresh-host demos, actualCLI support checks and actualMac/MintyIAB numbered recovery/keyboard confirmation/support guidance qualify this follow-on at application8716779. No actual-user validation or accessibility certification is inferred.
