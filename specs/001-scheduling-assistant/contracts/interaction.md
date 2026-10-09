# Interaction and interpretation contracts

Designed 2026-10-08. Applies equally to both interfaces. Authority: [spec](../spec.md), [model](../data-model.md), [service](scheduling-service.md).

## Planned command/configuration surface

- `PYTHONPATH=src python3 -m scheduling_assistant --model gpt-5.4-mini` starts genuine live conversation, discloses AI use and synthetic/local boundaries. Standard environment OPENAI_API_KEY is required; fail clearly without displaying its value. `--model` is explicit/configurable; do not silently substitute.
- `--api-base-url` defaults to loopback4010, `--scenario api_failure` is a clearly labeled optional local test flag. `--help` and missing configuration diagnostics need no model call.
- `reset` clears conversation/identity/consent; `quit` exits. Unknown action warnings remain after reset; exiting/restarting never certifies failure. EOF/interruption during write produces uncertainty if dispatch may have occurred.
- `.venv/bin/marimo run apps/scheduling_app.py --host 127.0.0.1 --port 28180` runs required UI. UI obtains model from explicit `SCHEDULING_MODEL` environment config, same key and loopback API default. No key fields or URLs exposing credentials.
- Planned demo guide uses `scripts/demo_scheduling.py --scenario success|failure` with scripted interpreter + actual supplied HTTP server. This is deterministic integration evidence, distinct from live model qualification.

## Shared session API

`Session.submit(text, event_id)` consumes one user turn and returns a typed view: disclosure, safe messages, displayed providers/slots, current proposal, outcome certainty, processing/error state and safe diagnostics. Event IDs are generated locally; duplicates return the prior view without reinterpreting/repeating effects. A serial controller prevents overlapping turns and marks writes in-flight before dispatch. Confirmation controls additionally bind the current proposal revision; stale controls cannot confirm a new proposal. Core checks remain required even when UI prevents double clicks.

CLI shows processing promptly, returned choices and exact proposal. Marimo uses submitted form values and immutable transcript snapshots; no effect runs merely because rendering cells rerun. Disable submissions while pending; retain independent browser-session conversation state. Render all text as escaped content, preserve clear labels/keyboard focus/status and AI disclosure. Only local reviewed theme/logo with source/use index; no tracking scripts/hotlinks or public distribution permission inferred.

## Interpretation boundary

`Interpreter.interpret(current_text, safe_context)` returns a locally validated structured value, not an instruction to call APIs. Context contains workflow intent/required next answer and supported enums, not private patient candidate objects/IDs, prior raw sensitive transcript or API key. The model may receive the current synthetic user input needed for extraction. No raw request/response/debug log.

Planned strict JSON extraction fields (all present, nullable where inapplicable, no additional properties):

| Field | Allowed interpretation |
| --- | --- |
| intent | provider_lookup, book, appointment_lookup, human, medical_advice, unsupported, unclear |
| specialty / location / appointment_type | nullable user-stated text; core validates supported scope, never turns unknown text into a supported guess |
| phone / dob / zip | nullable current-turn user answers; format validation and unique-match checks happen in code |
| start_date / end_date | nullable unambiguous ISO dates; ambiguity asks clarification |
| slot_choice | nullable displayed ordinal/reference from user; must resolve against current displayed returned slots |

No patientId, created slot facts, confirmed flag, action receipt or free-form user-facing medical answer is accepted. Model output is advisory. Schema/refusal/incomplete/model transport failures produce safe clarification or assistance and zero booking. Set Responses `store:false`, strict `text.format` JSON schema; parse returned output-text items only after completed status, handle refusal separately and cap output. Model errors do not authorize changing proposals or retrying writes.

Consent comes from actual user input, not model extraction. Permit standalone case-insensitive `yes`, `confirm`, `yes, book it` (trim surrounding whitespace/punctuation), only on a subsequent turn to the unchanged exact displayed proposal; mixtures with changes or conditions are ambiguous and need renewed confirmation. Dedicated UI confirm binds that same revision and generates a single user event. No medical advice or other unsupported prose from the model is shown verbatim; core renders truthful messages and returned scheduling facts.

## Diagnostics / human assistance

Allowlisted events: intent/state, operation enum, HTTP status/safe outcome, safe error/escalation reason, monotonic elapsed milliseconds. Exclude patient/slot/appointment identifiers, query strings, phone, DOB, ZIP, API key, transcript, patient response, model prompt/output and raw exception repr. Unit tests inspect success/error diagnostics and stdout/stderr for leakage. User-visible transient transcript is not a persisted diagnostic; reset clears it.

Human assistance says why the workflow stopped and advises contacting clinic scheduling staff. No invented telephone number, queued request, delivered transfer or clinician response. Advice/human/unsupported intent stops further scheduling calls. Correctable identity input gets bounded clarification; no-match/ZIP recovery must not loop indefinitely. UI and CLI may differ in presentation, never identity/consent/effect policy.
