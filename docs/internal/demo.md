# At-most-five-minute scheduling walkthrough

Updated 2026-10-09. This runbook covers actual implemented scheduling flows and design trade-offs. Live CLI and controlled IAB flows passed on macOS ARM and Minty Linux at `2efd0f6` with gpt-5.4-mini and the supplied synthetic API. Final application e0996c1 UI retests passed on both hosts; see canonical verification for the blocked additional latest-source CLI rerun. It is **not a completed recording**. See [video notes](video-notes.md) for capture ownership, pending metadata and evidence boundaries.

Prepare the owned API on 4010 and headless Marimo on 28180 using [setup](../user/setup.md). Configure live model/key in the process environment; keep credentials out of view. Reset the owned API before the happy take so slots are fresh, and reset the conversation between journeys. Use the controlled Codex in-app browser, approved local logo/theme, supplied synthetic inputs and normal-speed recording. Coordinate the shared capture slot; never overwrite a take.

## Test before video — recording OFF

Use the [current evidence/delta checklist](video-notes.md#test-before-video-current-source-versus-verified-baseline) first. Required Mac/Minty provider, booking, no-match and decline/reselect/separate-confirm/repeat/reset flows passed at `2efd0f6`. Additional Mac IAB duplicate ZIP, empty availability, advice/human/deferred lookup, conflict/repeat and outage checks passed. Those results do not qualify a later source revision automatically.

- Retest the uncommitted `neurology` fix in actual IAB: truthful unsupported guidance, no guessed specialty and no patient availability/booking.
- Passed actual IAB retest of supported CSS removal of the framework menu: input, Send, Confirm, Reset, focus, branding, status and transcript must remain usable. HTML export passed; PNG export stalled and is not claimed working.
- On the exact recording source, exercise the three required journeys with recording OFF and inspect the actual API request outcomes/POST count. Reset only owned synthetic state afterward.
- Obtain SM/Media's exclusive shared recording slot and Operator native recorder. The shared capture resource may involve Chrome, but the product must remain in controlled IAB. No video has been captured yet; missing recording capability remains explicit.

After these checks, record source/URL/time/reset/outcome metadata in video notes and start a fresh uniquely named native take. This is a practical regression/capture checklist, not a new scope or permission gate.

| Time budget | Show and explain |
| --- | --- |
| 0:00–0:20 | Purpose: explore providers, then control a synthetic appointment. Point to AI/synthetic disclosure; named primary-user and Support/Admin Personas remain pending. |
| 0:20–0:55 | Provider query and a location follow-up. Returned provider names/specialties/locations originate in GET/providers; no identity is requested. |
| 0:55–2:55 | Eight-turn booking below, including a decline, renewed selection, separate current consent and repeat without another booking. |
| 2:55–3:40 | Three-turn no-match journey below. Show truthful clinic assistance and “No handoff has been queued.” |
| 3:40–4:30 | Shared controller versus thin CLI/UI, strict AI extraction versus actual service facts, tests-first component work/integration and fixed review/UI findings. Link as-built diagrams/tests rather than replacing real UI with test output. |
| 4:30–5:00 | Process-local/unknown-write limits, deferred lookup/handoff, pending Persona validation and the teammate synonym exercise. Leave a stable closing handle. |

Include 2–3 second stable handles within these budgets. Rehearse to keep the assembled walkthrough at or under five minutes. If a real model/service delay or failure breaks the budget, record the true outcome and adjust the presentation; do not accelerate footage or imply an uncompleted operation succeeded.

## Exact synthetic turns

Provider lookup:

1. “Which primary care providers are downtown?”
2. “What about uptown?”

Reset the conversation before booking. Send each booking turn separately and wait for the actual response:

1. “I want to book primary care downtown.”
2. “My phone number is 555-0101.”
3. “My date of birth is 1985-04-12.”
4. “Choose the first option.” Read its returned provider, location and offset-bearing start time.
5. “No.” Verify the proposal is declined with no booking.
6. “Choose the first option.” Review the renewed exact proposal.
7. “Yes.” Show the actual returned appointment and booked outcome.
8. “Yes.” Show the known result without another POST.

Reset the conversation for the no-match failure:

1. “I want to book primary care downtown.”
2. “My phone number is 555-9999.”
3. “My date of birth is 1990-01-01.”

Show the truthful no-match/correction next step. If correction is unavailable, request clinic assistance; the assistant must not invent a record, fetch patient availability or claim a queued handoff. The qualifying three-turn failure is the no-match result; an extra assistance turn may be shown when useful without relabeling it as a service transfer.

## Technical reviewer checks

The genuine model interprets current text; deterministic code validates matching, returned slots and separate consent. Booking success requires a matching HTTP201 appointment. Conflict requires fresh choice/consent; unknown write outcomes forbid blind replay and survive conversation reset. Neither model extraction nor a UI control grants permission independently of the shared controller.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario success
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario failure
```

These demos use actual isolated HTTP service instances and a clearly labeled **scripted interpreter**; they are repeatable integration checks, not live AI or browser footage. Live CLI/UI host qualification is established at `2efd0f6`; final clone/release evidence is tracked in the native tasks. Latest unsupported-specialty and framework-menu UI deltas passed actual IAB retests on both hosts at e0996c1.

The [walkthrough](as-built/code-walkthrough.md) names the small tests-first specialty-synonym exercise and exact verification commands. [Architecture](as-built/architecture.md), [decisions](../product/decisions.md), [milestones](milestones.md) and [next steps](../product/next-steps.md) supply supporting detail. Capture may continue after the coding checkpoint; no assigned-window compliance statement is established.
