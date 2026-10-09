# Code walkthrough

Updated **2026-10-09**. Reviewed application source: **`e0996c1c8a438b6b6bfeff5283b5b3b02ddd8e69`**. Both fresh Mac/Minty clones passed 114 tests and both demos; the qualification owner completed genuine final-source IAB provider/booking/reset/no-match/unsupported-specialty flows on both hosts. Prior genuine CLI evidence remains at its recorded revisions; an additional latest-source CLI rerun was blocked by automatic approval review for credential-use authorization. See [verification](../scheduling-verification.md) for that explicit gap. This document describes actual symbols, not a duplicate completion ledger; [native tasks](../../../specs/001-scheduling-assistant/tasks.md) own progress.

## Start at the boundary you need

| Concern | Actual entry points | Behavior tests and caution |
| --- | --- | --- |
| Terminal construction and one-turn loop | [`__main__.py`](../../../src/scheduling_assistant/__main__.py): `main`, `_session`, `Configuration` | [`test_scheduling_interfaces.py`](../../../tests/test_scheduling_interfaces.py): help/configuration make no model call; fixed safe errors; unique events/revisions; actual controller separate-consent/single-booking parity. CLI renders `View.text`; it cannot authorize a POST itself. |
| Browser construction and submitted controls | [`scheduling_app.py`](../../../apps/scheduling_app.py): Marimo cells; [`ui_bridge.py`](../../../src/scheduling_assistant/ui_bridge.py): `configured_bridge`, `UIBridge.submit`, `render_html`, `UISnapshot` | [`test_scheduling_ui.py`](../../../tests/test_scheduling_ui.py): duplicate/stale/overlapping events, escaped transcript, session isolation, reset history and proposal confirmation. Callbacks consume turns; reading/rendering state performs no scheduling. Actual final-source controlled IAB journeys passed on both fresh hosts. The actual Marimo callback/scheduler test verifies controls rebuild after submission. |
| Immutable returned facts and action ownership | [`domain.py`](../../../src/scheduling_assistant/domain.py): `Preferences`, `Patient`, `Provider`, `Slot`, `Appointment`, `Proposal`, `View`, `ActionLedger`, `PROCESS_ACTIONS` | [`test_scheduling_core.py`](../../../tests/test_scheduling_core.py): invalid facts/dates, frozen snapshots, already-claimed actions and process-level unknown guard. Do not replace returned facts with model-generated ones. |
| Consent and exact effect comparison | [`core.py`](../../../src/scheduling_assistant/core.py): `affirmative`, `choose_slot`, `matching_appointment`, `slot_description` | Core tests require standalone consent, current displayed slot membership and matching patient/provider/specialty/location/time/status. A selected option is not consent. |
| Conversation, identity and recovery | [`session.py`](../../../src/scheduling_assistant/session.py): `Session.submit`, `_advance`, `_select`, `_book`, `_context`, `_call`, `_emit` | [`test_scheduling_session.py`](../../../tests/test_scheduling_session.py): identity before availability, private duplicate ZIP, fresh ZIP after phone/DOB changes, clearing prior appointment binding on identity changes, bounded no-match correction, missing-answer-only prompts, conflict exclusion lifecycle, declined/mixed consent, refusal, unknown writes and interruption. `UnsupportedScopeTests` covers committed DomainError assistance with no gateway calls. All interfaces use this owner. |
| Advisory AI extraction | [`interpretation.py`](../../../src/scheduling_assistant/interpretation.py): `Interpretation`, `Interpreter`, `ModelError`; [`openai_adapter.py`](../../../src/scheduling_assistant/openai_adapter.py): `OpenAIInterpreter.interpret`, `_schema`, `_context` | [`test_scheduling_ai.py`](../../../tests/test_scheduling_ai.py): strict fields/no authority fields, current-turn safe context, bounded output, no redirects/retries, refusals/incomplete/malformed responses and completed reasoning before structured output. Never show arbitrary model output as scheduling evidence. |
| Supplied service HTTP boundary | [`scheduling_api.py`](../../../src/scheduling_assistant/scheduling_api.py): `SchedulingAPI.providers`, `find_patients`, `availability`, `book`, `_request`, `APIError` | [`test_scheduling_api.py`](../../../tests/test_scheduling_api.py): loopback-only URLs, exact query/body encoding, strict response facts, bounded transport, HTTP201 matching, recognized rejections and uncertain POST responses. No automatic write retry. |
| Safe local diagnostics | [`diagnostics.py`](../../../src/scheduling_assistant/diagnostics.py): `Diagnostics`; controller `_call`/`_emit` | [`test_scheduling_diagnostics.py`](../../../tests/test_scheduling_diagnostics.py) and session diagnostics tests: enum/timing allowlist, detached bounded snapshots, private values excluded and sink failure cannot change an action. Both configured interfaces inject Diagnostics, and safe escalation reasons are tested. No raw prompt, query, identity, key or exception logging. |
| Real local service and repeatable demos | [`server.py`](../../../vendor/scheduling-reference/mock-api/server.py): supplied `Store`, `Handler`; [`demo_scheduling.py`](../../../scripts/demo_scheduling.py): `SuppliedServer`, `ScriptedInterpreter`, `run` | [`test_scheduling_integration.py`](../../../tests/test_scheduling_integration.py): actual HTTP happy/no-match/duplicate/conflict/outage/stale/committed-but-lost response; demos label scripted interpretation and clean up isolated services. These tests do not prove live AI/browser behavior. |

Supplied source/fixtures stay unchanged under [`vendor/scheduling-reference`](../../../vendor/scheduling-reference/PROVENANCE.md). The browser loads the approved local [logo](../../../assets/ui/branding/ochsner-health.svg) and [theme](../../../assets/ui/themes/ochsner.css); [`ui-assets.md`](../ui-assets.md) records provenance. The app adds focus styles, an AI/synthetic disclosure, a processing spinner/status and escaped transcript rendering. Its state permits callback self-reruns to rebuild controls; rerendering does not replay submitted effects. The current app hides only Marimo’s `data-testid="notebook-actions-dropdown"` framework menu, whose export actions are outside this scheduling demonstration; this is not a security control. Actual final-source IAB rehearsal covered that presentation on both hosts.

## Follow one booking through the code

`__main__._session` or `configured_bridge` constructs the live model adapter and loopback gateway, then injects both into `Session`. Each submitted turn gets a local event ID and expected revision. `Session.submit` serializes it, returns cached duplicate results and rejects stale controls before interpretation. Reset clears conversation facts while retaining the process action ledger.

`OpenAIInterpreter.interpret` sends current synthetic input plus limited workflow context through a strict Responses JSON schema with `store:false`. The resulting immutable `Interpretation` has no authorization/result fields. Explicit unsupported-specialty examples preserve the supplied value and stop unsupported intent; `test_wire_instructions_teach_unsupported_specialty_without_dropping_it` protects the request contract, while actual “Book neurology” model/UI retests establish observed behavior. `_advance` validates preferences and privately searches exact phone+DOB. Duplicate records require a local ZIP match; candidates are never rendered or placed in model context. Phone/DOB changes clear any earlier ZIP; identity/preference changes clear proposal/options, previous appointment presentation and conflict exclusions. Prompts ask only for missing identity fields. Two unsuccessful searches exhaust the one correction opportunity until reset. Provider discovery bypasses patient matching entirely.

Only a uniquely matched patient can reach availability. The HTTP adapter validates returned available slots and filters before the controller displays them. `_select` binds one displayed slot and patient to an immutable `Proposal`. `_book` is reachable only on a later standalone affirmative turn for the unchanged proposal. The ledger claims that action before dispatch. Only a matching typed appointment from HTTP201 produces completed output.

A recognized conflict records a known rejection, excludes the rejected slot, refreshes availability and requires a new choice/confirmation. Lost, malformed or mismatched write results retain unknown certainty and prevent another booking even after reset. Interrupted dispatch sets the guard before propagating interruption. Advice, human-help and unsupported/lookup requests stop scheduling with truthful clinic guidance; recorded handoff is not implemented. The DomainError branch also supplies specific supported-specialty/location/date/type guidance before clinic assistance, without any gateway call for the invalid request.

## Run the current interfaces and checks

First follow [setup](../../user/setup.md), including interpreter/version verification, environment configuration and ownership checks for ports4010/28180. Commands below assume the owned reference API is running and live credentials are present for the interfaces:

```sh
.venv/bin/python -m scheduling_assistant --model gpt-5.4-mini \
  --api-base-url http://127.0.0.1:4010
.venv/bin/marimo run apps/scheduling_app.py --headless \
  --host 127.0.0.1 --port 28180
```

The UI reads `SCHEDULING_MODEL` and `SCHEDULING_API_URL`; the CLI also accepts `--api-url`. No automatic browser launch is needed. Controlled Codex in-app browser qualification and source recording are independent of importing the Marimo app in tests.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario success
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario failure
.venv/bin/marimo check --strict apps/scheduling_app.py
```

The demos use fresh reference `Store` instances and ephemeral ports; they do not mutate the visible service on4010. For exact current genuine AI execution and host evidence consult [verification](../scheduling-verification.md); [video notes](../video-notes.md) distinguish tested flows from recordings. Final-source IAB flows passed on both hosts. Genuine CLI journeys at `2efd0f6` and CLI timing at `947e621` are recorded separately from the blocked additional latest-source CLI rerun. Test-double results are not live model evidence. Synthetic matching is not authentication; the ledger is process-local and cannot reconcile an uncertain effect after restart.

## Small teammate change: a clear specialty synonym

Practice extending the interpreter's explanation so “family medicine” clearly maps to the existing `primary_care` specialty. Keep the supported API enums, controller, patient matching and consent policy unchanged. The edit belongs in `openai_adapter.py`'s `_INSTRUCTIONS`; it adds language understanding guidance, not an endpoint or permission.

1. Before editing the prompt, add a failing test to `test_scheduling_ai.py` that captures the actual outgoing request instructions and requires the explicit synonym mapping. Keep the existing unknown-specialty preservation assertion and no-authority schema checks. This verifies the configured instruction, not model semantic accuracy.
2. Add the minimal instruction, then run `PYTHONPATH=src .venv/bin/python -m unittest tests.test_scheduling_ai -v` and the full suite/demos above. Existing consent and failure tests must stay green.
3. Separately qualify the synonym with the genuine model in a synthetic provider lookup against the owned API. Check actual returned provider filters and confirm it asks for no identity. Record the measured outcome truthfully; a transport test double cannot establish language understanding.

Do not add “family medicine” to API enums, infer a patient/slot identifier, bypass confirmation or broaden unsupported specialties. If the genuine model still cannot interpret the wording reliably, preserve safe clarification and record the limitation.

See [architecture](architecture.md) for the component view, [decisions](../../product/decisions.md) for trade-offs, [milestones](../milestones.md) for immutable checkpoints and [next steps](../../product/next-steps.md) for the remaining handoff.

Both diagrams in [architecture](architecture.md) rendered as SVG and were visually inspected in controlled IAB with pinned Mermaid 11.12.0. Disposable rendering added no repository/global dependency; screenshots remain outside Git.
