# MVP design decisions

Updated 2026-10-08. Approved lane: genuine AI interpretation, supplied reference scheduling API, deterministic identity/consent/effects, CLI and thin Marimo text interface.

- Assignment Required/Good-to-have and policies/OpenAPI determine scope; suggested scenario priorities do not make appointment lookup mandatory. Booking duplicate matching remains required. Existing lookup is deferred.
- The model interprets text and preferences. Code verifies phone+DOB, resolves duplicate matches privately by ZIP, validates returned slots and binds explicit current consent to the exact patient/slot. Provider lookup needs no identity.
- Only valid HTTP201 booking evidence supports booked output.409 requires a fresh choice/confirmation. A timeout, malformed or mismatched write result is unresolved and blocks blind POST retry. No durable idempotency is claimed.
- Use the supplied reference server and fixtures in a private selective vendor copy with provenance. Original intake/metadata remain ignored. Each candidate/test has independent in-memory booking state.
- Latest Operator clarification retains the original MVP lane scope. No rules engine is added solely due to the superseded all-lanes engine relay. The MVP uses its small deterministic safety boundary; scalable engine demonstrations belong in the originally scoped candidate lanes.
- Runtime accepts environment OPENAI_API_KEY and an explicit configurable model. Shared account capability evidence supports gpt-5.4-mini; candidate-specific live flows still require qualification. No Bitwarden runtime dependency or raw prompt/transcript/identity/secret logging.
- Use approved cached Ochsner logo/colors only for internal review. No public distribution grant. UI loopback28180; independent reference API4010; check ports before binding.
- State is process-local. Mock identity matching is not production authentication. Operator owns effort-window compliance and public submission. No unsupported assigned-window/readiness claim.
