# Prototype limitations

Updated2026-10-09. This is an internal synthetic scheduling demonstration using genuine AI interpretation and the supplied independent reference API. Matching phone/DOB and private ZIP is not authentication. No real patients, production scheduler, database or durable session/idempotency are included.

Existing appointment retrieval (conditional US5.1–2), service-recorded handoff, rescheduling, cancellation, new-patient registration, medical advice/triage and an admin console are deferred or unsupported. The required US5.3 guidance stops the workflow and directs you to clinic scheduling staff. No human request is queued or delivered by this application. Duplicate-match booking protection remains implemented and required. Canonical acceptance: [feature spec](../../specs/001-scheduling-assistant/spec.md).

Only returned available slots can be selected.409 requires a fresh choice and consent. An unknown booking outcome must be verified with clinic staff before retry; reset or restart does not prove failure. Read [recovery](../internal/scheduling-recovery.md). Data and guards are process-local; concurrent production booking and cross-session replay are not guaranteed. The mock uses relative dates and fixed-05:00 offsets.

Named/pinned primary-user and Support/Admin Personas remain pending validation. Actual browser/fresh-host checks and recording status are in [verification](../internal/scheduling-verification.md). Passing tests or prepared video notes are not production readiness, a finished video or proof of the assignment's coding-window compliance.
