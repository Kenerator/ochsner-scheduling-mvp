# Conversation and recovery

Updated 2026-10-09. Use only the supplied synthetic fixtures. Both interfaces send turns to the same controller; the model extracts answers while code owns identity, slots, consent and effects. See [setup](setup.md) for launch commands. These are reproducible instructions, not a claim that live UI qualification is finished.

## Provider discovery

Ask “Which primary care providers are downtown?” Follow up with “What about uptown?” Provider lookup uses returned API facts and needs no patient identity. Supported specialties are primary care and dermatology; supported locations are downtown, uptown and lakeside. Other specialties, locations and appointment types need clinic assistance.

## Book a synthetic appointment

1. Ask to book primary care downtown.
2. Supply synthetic phone `555-0101` and date of birth `1985-04-12` when requested. No patient-specific availability is fetched until matching succeeds.
3. Read the actual returned slots. Choose a currently displayed option by its number, such as “first.”
4. Read the exact proposed provider, specialty, location and start time. Send **yes** in a separate message to book that proposal, or **no** to decline.
5. A validated matching HTTP201 response produces “Booked appointment.” A selected slot or confirmation prompt alone is not a booking.

“Confirm” and “yes, book it” also work as standalone confirmation. Changes or conditions in a confirmation do not authorize a booking. Changing identity/preferences invalidates the old proposal. Repeating the same submission or saying yes again after completion does not create another appointment.

For private duplicate matching, use synthetic phone `555-0130` and date of birth `1978-09-22`; supply ZIP `70115` when asked. Candidate records are not displayed, and ZIP is checked locally against the returned matches.

## Failures and next steps

| Situation | Expected behavior |
| --- | --- |
| No match: `555-9999`, `1990-01-01` | One correction opportunity, then clinic assistance; no patient availability or booking. |
| Dermatology at lakeside | Truthful empty availability; choose another supported filter or contact staff. |
| A displayed slot becomes unavailable | HTTP409 refreshes availability and excludes the rejected slot; a new choice and separate consent are required. |
| CLI `--scenario api_failure` | Service outage message and clinic assistance; no fabricated result. |
| Model failure/refusal or invalid response | Safe clarification; pending consent cannot be used to book. |
| Booking response lost/malformed/mismatched | Outcome **unknown**; stop and ask clinic scheduling staff to verify, without retrying. |
| Medical advice, human help or existing appointment lookup | Scheduling stops with truthful scope/assistance guidance. |

No handoff has been queued or delivered. Existing appointment lookup and service-recorded handoff are deferred. The assistant gives no medical advice or triage and invents no clinic telephone number.

CLI commands: `reset` clears the conversation; `quit` exits. The UI uses submitted turns and shows a transcript. Reset clears transient identity/consent/display history, while a process-local unknown-write guard remains active. Exiting or restarting does not reconcile an unknown effect. The API holds bookings only in memory; restart only the owned reference process to reset synthetic demo data.

## Limits

This PoC has synthetic matching rather than production authentication, process-local state rather than durable idempotency, and no automatic unknown-write reconciliation. Current-turn synthetic text is sent to the configured OpenAI service; prior raw identity history and patient candidates are excluded from model context. Diagnostics contain allowlisted enums/timings, not raw prompts, identity, keys or exceptions. Browser transcripts are transient user-visible content, so keep captures synthetic.

[Tested evidence and capture limitations](../internal/video-notes.md), [authoritative task progress](../../specs/001-scheduling-assistant/tasks.md) and [next steps](../product/next-steps.md) remain separate from these instructions.
