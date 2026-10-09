# Scheduling verification

Updated 2026-10-09, macOS ARM, Python3.12.12, Marimo0.25.0. Reviewed source: planning baseline `cc4535d` plus the current uncommitted scheduling package, interfaces and tests. Final revision and fresh-host results remain pending. Native [tasks](../../specs/001-scheduling-assistant/tasks.md) own progress.

Automated verification uses `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`. The combined suite passed109 tests after the four independent-review fixes and the real Marimo callback regression. The supplied service integration runs fresh Store instances on owned ephemeral loopback ports and shuts them down. API25, AI11 and supplied-server integration8 tests passed independently. These are synthetic tests, not live model qualification.

The success and failure commands in [setup](../user/setup.md) both passed. Success uses a **simulated interpreter with actual supplied HTTP**, seven turns, GET providers/search/availability200 and exactly one POST appointments201, including decline before later separate consent. Failure uses the same disclosed simulation with actual HTTP, three turns, providers/search200, zero availability/POST and clinic assistance. No generic starter demo is scheduling evidence.

## Genuine model execution

All live runs used explicitly selected `gpt-5.4-mini`, direct Responses strict extraction, authorized process-local runtime credentials and supplied synthetic inputs. No key or raw transcript is retained here. Single user, sequential turns; no load benchmark.

| Environment/interface | Scenario | Observed result |
| --- | --- | --- |
| Mac ARM, shared Session, fresh ephemeral API | Provider, two turns | providers → providers; two GET providers200;2.438s total |
| Mac ARM, shared Session, fresh ephemeral API | Booking, eight turns | identity → identity → slots → confirmation → declined/slots → confirmation → completed → completed; one search200, availability200 and POST201;8.724s total |
| Mac ARM, shared Session, fresh ephemeral API | No match, three turns | identity → no_match → assistance; two search200;zeroPOST;3.163s total |
| Mac ARM, actual CLI, API4010 | Provider, two turns | exit0, actual returned providers; two GET providers200 |
| Mac ARM, actual CLI, API4010 | Booking, eight turns | exit0; one booked message, retained success on repeat; search200, availability200, exactly one POST201 |
| Mac ARM, actual CLI, API4010 | No match, three turns | exit0, clinic guidance; two search200, zeroPOST |
| Mac ARM, actual IAB/Marimo28180 | Provider first turn | actual providers200/result; browser found controls disappeared after spinner; fixing before further qualification |

Reference API4010 started by this task at00:19CDT; no unrelated listener terminated. Headless Marimo launch was initially denied by automatic approval review for missing credential-effect authority; direct user authorization resolved it. Started the live UI at00:27CDT; controlled IAB only. Callback to SM remains separately denied; no workaround used. Times here are approximate observations, not exact capture timestamps.

## Safety/review evidence

One independent combined review found stale ZIP reuse after phone/DOB change, prior completed appointment binding surviving identity/preference changes, missing configured UI diagnostics and missing escalation reasons. All four have targeted regressions and fixes; final combined checks remain pending. Additional actual-browser controls disappearance is tracked separately and is not a passed UI journey.

Tests also exercise actual committed201 with a dropped response: outcome unknown, no secondPOST after reset. Matching uses phone/DOB and private local ZIP, not authentication. Invalid/mismatched201 is unknown;409 refreshes alternatives and requires fresh choice/consent;503 is truthful rejection. No recorded handoff is implemented.

## Remaining qualification

Finish real IAB provider/booking/no-match, multi-tab isolation, keyboard/focus, elapsed/feedback observation and reset. Verify fresh authenticated private GitHub clones on Mac ARM and Minty Linux x86_64, declared dependency install, tests, demos and live interfaces. Finalize actual-code diagrams/navigation and revision stamps. Actual continuous UI recording is not available through the currently exposed browser APIs; coordinate an Operator-assisted native recorder with SM before capture. No recording, benchmark compliance, production readiness or assigned-window compliance is claimed.

## Local IAB result after callback repair

Controlled IAB on macOS ARM completed provider lookup in two turns, then booking in eight turns with separate phone/DOB, returned slot, decline, reselect, dedicated current confirmation and repeated yes. API4010 returned search200, availability200 and exactly one POST201 for that UI booking. Reset cleared the displayed transcript; no-match in three turns performed two search200 and noPOST, ending with truthful clinic guidance/no queued handoff. A second IAB tab had a fresh transcript; Tab reached Send, Return on blank input showed validation without scheduling. The original missing-controls bug is fixed via Marimo state self-rerun, with a failing-then-passing real callback/scheduler regression. Actual screenshot evidence is held outside Git; it is not continuous video.
