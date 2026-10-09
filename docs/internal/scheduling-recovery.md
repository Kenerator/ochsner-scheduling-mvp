# Scheduling recovery

Updated2026-10-09 from [Session](../../src/scheduling_assistant/session.py), [HTTP adapter](../../src/scheduling_assistant/scheduling_api.py) and actual supplied-service [integration tests](../../tests/test_scheduling_integration.py). Evidence: [verification](scheduling-verification.md).

A proposal is not a booking. Only a validated201 appointment matching the resolved patient and every returned slot detail is completed. Standalone consent must follow the displayed proposal in a separate turn. Changed identity/preferences/choice, decline, reset, refusal or model failure invalidate consent. Duplicate events and repeated success confirmation do not dispatch again.

A recognized contract rejection is known rejected. A409 refreshes availability, excludes that rejected slot during recovery and requires a fresh choice and confirmation. A503 gives clinic scheduling guidance; no queued human handoff is claimed. Missing identity, no match, unresolved duplicate ZIP, unsupported scope, advice requests and empty results do not authorize booking.

A timeout/disconnect after dispatch, malformed/mismatched write response or interruption may mean the booking committed. The outcome stays **unknown**, blocks new booking attempts at process scope and survives conversation reset. Ask clinic scheduling staff to verify the outcome before another attempt. There is no automatic reconciliation endpoint or clear-unknown control. Restarting the process loses this volatile guard; it does not establish that the previous write failed. Restarting the owned mock resets synthetic server state only.

Diagnostics retain bounded allowlisted state, intent, operation, outcome, fixed reason and elapsed milliseconds in process memory. They exclude prompt/transcript/query/body/IDs/phone/DOB/ZIP/key/raw exception text. The transient user-facing transcript necessarily includes supplied synthetic answers and returned facts; reset clears its display. No production privacy, authentication or durable idempotency claim is made. Support/Admin Persona selection is pending; this documentation and safe diagnostics supply the current support surface without a console.
