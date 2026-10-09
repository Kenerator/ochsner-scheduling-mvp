# User Stories — native specification index

Updated 2026-10-09. Native [specification](../../specs/001-scheduling-assistant/spec.md) owns reconciled stories and acceptance detail; [tasks](../../specs/001-scheduling-assistant/tasks.md) own implementation progress. This index replaces migrated draft detail. Inferred wording/basis is separate from acceptance and supplies no permissions.

Source background: [client intake index](RFP/README.md). No named, pinned primary-user or Support/Admin Persona was supplied. Both mappings remain unresolved in [Personas](personas.md); synthetic patient fixture names are not substitute Personas. These pending mappings neither invent a console nor gate the accepted implementation.

| Canonical native story | Origin / basis | Accepted scope / Persona mapping |
| --- | --- | --- |
| [US1 Find providers](../../specs/001-scheduling-assistant/spec.md#user-story-1---find-providers-priority-p1) | Inferred wording from supplied assignment Required 1–3/provider journey | Required; primary-user Persona pending |
| [US2 Confirm and book](../../specs/001-scheduling-assistant/spec.md#user-story-2---confirm-and-book-an-appointment-priority-p1) | Inferred wording from supplied required booking journey and policies | Required; primary-user Persona pending |
| [US3 Resolve identity and obtain help](../../specs/001-scheduling-assistant/spec.md#user-story-3---resolve-identity-safely-and-obtain-help-priority-p1) | Inferred wording from supplied no-match/duplicate/failure scenarios and policies | Required identity/failure safety; primary-user Persona pending |
| [US4 Inspect safe recovery context](../../specs/001-scheduling-assistant/spec.md#user-story-4---inspect-safe-recovery-context-priority-p2) | Inferred Support/Admin background seed reconciled with required observability/documentation | Required diagnostics/recovery documentation; Support/Admin Persona pending; no admin console or delivery permission |
| [US5 Existing appointment lookup](../../specs/001-scheduling-assistant/spec.md#user-story-5---look-up-existing-appointments-priority-p2-optional-deferred) | Inferred wording from supplied optional journey | Lookup deferred by explicit scope decision; truthful unsupported assistance remains required; duplicate-match protection stays in booking |

[Accepted scope](../../specs/001-scheduling-assistant/scope-decisions.md) preserves provider lookup, private matching, returned slots, exact current confirmation and truthful effects in genuine CLI/Marimo interaction. Recorded handoff remains optional/deferred; assistance is clinic guidance without a claimed transfer. [Usage](../user/usage.md) gives current synthetic flows and [video notes](../internal/video-notes.md) separate demonstrated execution from recording status.
