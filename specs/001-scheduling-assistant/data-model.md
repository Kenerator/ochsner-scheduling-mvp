# Data model

Designed 2026-10-08; planned Python types, not persisted schemas. Authority: [spec](spec.md), [service contract](contracts/scheduling-service.md), [interaction](contracts/interaction.md).

## Entities and validation

| Entity | Fields and relationships | Validation / privacy |
| --- | --- | --- |
| Conversation | opaque local session ID, generation, intent, preferences, identity state, displayed options, proposal, outcome, processed event IDs | Session-local, serial updates; no cross-session history promise; no raw transcript logging |
| Preferences | specialty, optional location/startDate/endDate, appointment type if supplied | Accepted enum only; actual ISO calendar dates and start<=end; unsupported types stop workflow; changes invalidate displayed options/proposal |
| Identity input | phone, DOB, optional ZIP | Validate nonempty phone and ISO calendar DOB; preserve supplied phone format for exact service match; ZIP string preserves leading zeros; memory only |
| Patient candidate | patientId, phone, dateOfBirth, zipCode; optional returned name/establishedPatient | Valid typed service result, no user-selected IDs; candidates private, never logged or passed to model; phone/DOB match query |
| Resolved identity | patientId, identity generation | Exactly one validated candidate from search/ZIP; input changes invalidate identity and proposal; matching is not authentication |
| Provider | providerId, name, specialty, locations[], modalities[] | Returned typed fields, unique IDs, matching requested filters; no inference of availability |
| Slot snapshot | slotId, providerId, specialty, location, startTime, available | Returned available=true, unique IDs, valid offset date-time, matching filters; displayed with supplied offset; snapshots can become stale |
| Booking proposal | opaque proposal ID/revision, session and identity generations, resolved patientId, immutable slot snapshot, displayed-at turn | Bound to displayed returned slot and resolved patient; new patient/preference/slot supersedes it; IDs are internal, not model authority |
| Action record | proposal ID, attempted/in-flight/completed/known-rejected/unknown certainty, optional returned appointment, safe reason | Atomic transition before POST; immutable success retained; unknown guard persists at process scope across conversation reset |
| Appointment | appointmentId, patientId, providerId, specialty, location, startTime, status | Only HTTP201, nonempty ID, scheduled status, exact patient and all available slot detail comparisons; API has no slotId in result |
| Recovery context | safe reason code, certainty, next step, rejected slot IDs for current recovery | No sensitive summary; no queued/delivered claim; uncertainty survives reset as safety warning |
| Diagnostic event | operation name, state/intent, HTTP status or safe outcome, safe error/escalation code, durationMs | Explicit allowlist; no query/body/transcript/IDs/phone/DOB/ZIP/secrets/raw exception text |

Typed response validators must reject absent arrays, wrong types, duplicate identifiers, invalid dates, inconsistent filters and missing fields necessary for safe use. Ignore unrelated service fields; do not surface fixture-only metadata. Valid zero-length arrays are meaningful empty results, not transport errors.

## State transitions

| State / event | Guard and transition | Effect |
| --- | --- | --- |
| Start -> provider request | supported preferences, missing details asked as needed | GET providers; no identity questions |
| Start -> booking | collect phone/DOB | GET patient search |
| Search -> no match | matches empty | one correction opportunity then human assistance; no patient-specific call |
| Search -> duplicates | multiple validated matches | ask private ZIP, retain private candidates |
| ZIP -> unresolved | zero or multiple exact candidates after one clarification | assistance; no disclosure or booking |
| Identity resolved -> search slots | supported specialty, optional filters | GET availability; show only validated available returned slots |
| Slots -> proposal | user selects displayed index/reference | render exact slot details and ask confirmation; no POST |
| Proposal -> ambiguous/decline/change | only subsequent standalone affirmative to current unchanged proposal allowed | no POST; decline clears proposal; changes require refreshed proposal/confirmation |
| Proposal -> in-flight | matching generations, current displayed slot and explicit affirmative, no unknown guard | atomically claim action and POST once |
| In-flight -> completed | validated exact HTTP201 result | render returned appointment; repeated confirmation reuses result |
| In-flight -> conflict | received HTTP409 | invalidate consent, remember rejected slot, GET fresh availability, require new choice/confirmation |
| In-flight -> known rejection | received valid contract error (400 or supplied 503) | safe reason and assistance/correction; no automatic write retry |
| In-flight -> unknown | transport/interruption after dispatch, unexpected response/status, malformed/mismatched201 | no success/failure assumption; process guard blocks booking, advise human verification |
| Any -> advice/human/unsupported | interpretation indicates unsupported intent or policy refusal | stop scheduling; truthful assistance, no clinical output |
| Any -> reset | explicit reset, not an inferred model action | clear identity/choices/consent/transcript; retain unknown guard/warning |

Interruptions after a POST may have reached the server are unknown. Before dispatch, local validation/model failure means no write attempted. A process restart loses volatile guards; startup/recovery documentation must warn that it does not resolve prior uncertainty. The MVP offers no durable reconciliation system or control that silently marks an unknown booking failed.
