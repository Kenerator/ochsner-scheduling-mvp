# Video production notes

Updated **2026-10-09**. This is the canonical MVP capture handoff and overview script context. Genuine live CLI and controlled Codex in-app browser qualification on macOS ARM and Minty Linux passed provider lookup, multi-turn confirmed booking and no-match assistance at source `2efd0f6` with **gpt-5.4-mini** and the actual supplied synthetic HTTP service. **Recording remained OFF during qualification; no continuous UI recording has been saved.** The available automation surface has no supported recorder API; Operator native recording is the fallback. Capture may continue after the three-hour checkpoint; no assigned-window compliance or finished-video claim is made.

## Product, audience and evidence

The assistant helps a user explore returned providers without identity, then privately match a synthetic record and control an exact booking. [US1–3](../product/user-stories.md) hold this coverage; [US4](../../specs/001-scheduling-assistant/spec.md#user-story-4---inspect-safe-recovery-context-priority-p2) supports safe diagnosis/recovery through code and documentation, not an admin console. Named, pinned primary-user and Support/Admin Personas remain pending in [Personas](../product/personas.md). Fixture names are not validated Personas.

The implemented Python stack is a reusable `Session` controller, immutable domain facts/action ledger, direct strict Responses interpreter, standard-library scheduling HTTP adapter, thin CLI and Marimo 0.25.0 form/transcript. No added backend, database or rules engine. Approved local Ochsner logo/theme are visible in the UI. See [walkthrough](as-built/code-walkthrough.md), [architecture](as-built/architecture.md), [assets](ui-assets.md) and [decisions](../product/decisions.md).

Native Specify, Clarify, Plan, Tasks and read-only Analyze informed implementation; all three Analyze findings were fixed. Behavior tests preceded component work; disjoint owners worked in parallel and integrated against the supplied service. Independent review's four findings were fixed, as was a real Marimo callback regression. Combined test runs reached 109 then 112 passing tests; these counts describe those runs, not a permanent final release count. Actual live model/UI execution is separate evidence from injected-interpreter tests and the explicitly scripted HTTP demos.

Checkpoint `a1af7ca`, annotated tag `poc/checkpoint-2h-20261009`, records the clean source checkpoint at **00:42:38 CDT** against the advisory **00:41:01 CDT** target and the then 97-test slate. Subsequent corrections/qualification belong to later source commits; capture filenames must use the actual recorded commit. Live CLI/UI checks on both hosts are recorded at `2efd0f6`; final fresh-clone/release evidence belongs in the native tasks. Latest application e0996c1 passed actual IAB provider/booking/no-match and unsupported-specialty retests on both hosts; recording remained OFF. See [milestones](milestones.md) and [tasks](../../specs/001-scheduling-assistant/tasks.md) for final source/evidence reconciliation.

## Test before video: current source versus verified baseline

Complete the latest-delta checklist with recording **OFF** before a take. A pass at `2efd0f6` does not automatically qualify later uncommitted behavior. No footage or capture file exists yet.

| Control/scenario | Verified baseline or current status | Before recording |
| --- | --- | --- |
| Live provider, booking and no-match in CLI/UI on Mac and Minty | Passed at `2efd0f6` | Recheck on the exact commit used in the take. |
| Decline → reselect → separate current confirmation → repeat guard; reset | Passed live at `2efd0f6` | Verify Send, Confirm and Reset controls still work and no extra POST occurs. |
| Mac duplicate match / ZIP `70115`; dermatology/lakeside empty slots | Passed actual IAB | Preserve private matching and truthful empty-result output. |
| Mac advice, human request and deferred appointment lookup | Passed actual IAB | Preserve scope guidance and no fabricated handoff. |
| Mac permanent conflict trap / repeat without POST; service outage | Passed actual IAB | Preserve fresh-choice/consent and truthful outage behavior. |
| HTML export / PNG export | HTML passed; PNG stalled | Do not present PNG export as working or use it as video evidence. |
| Framework menu presentation | PASS at e0996c1: supported stable CSS hides framework menu on both hosts | Actual IAB verified branding, input, Send, Confirm, Reset and readable transcript/status after the change. |
| Unsupported specialty `neurology` | PASS at e0996c1: genuine model request stops with unsupported-scope/clinic guidance on both hosts | Real request retested; no guessed supported specialty, availability or booking. |

The current recording boundary is **a coordinated exclusive shared recording slot and native recording capability**. SM coordinates the shared Chrome/desktop capture resource; product interaction remains in controlled Codex IAB and does not authorize a Chrome product-browser fallback. Operator/native capture remains necessary because the automation recorder API is unavailable.

Before changing recording to ON:

1. Confirm the exact source commit, clean intended source state, owned API 4010/UI 28180 and fresh synthetic fixture state. Resolve latest pending rows above through actual UI checks; record failures honestly.
2. Confirm no credentials, private tabs or non-synthetic patient content are visible. Verify AI disclosure, logo/theme, keyboard focus, processing status, returned slot detail and transcript readability.
3. Run provider, happy booking and no-match once with recording OFF. Inspect actual API operations: no identity for provider lookup; no POST before separate current consent; one matching 201; no replay on repeat; no patient-specific availability/booking on no-match.
4. Reset only owned demo state, reserve the exclusive SM/Media recording slot, confirm the native recorder and unused destination filename, then start the actual take. Leave 2–3 second stable handles and keep normal speed.

## Required actual UI takes

Use the [at-most-five-minute runbook](demo.md). Record silent synthetic UI at normal speed, readable full interface, with 2–3 seconds of stable opening/closing handles. Controlled Codex in-app browser only; no Chrome fallback. Coordinate the shared desktop/IAB recording slot with SM/Media before starting. Native MOV/MP4 H.264 at 1920×1080 or larger and 30 fps is preferred; native WebM is accepted without forced conversion. No test-output substitution or fabricated footage.

| Scenario label | Required visible outcome | Execution qualification | Recording status |
| --- | --- | --- | --- |
| `provider-lookup` | Multi-turn query, returned GET/providers facts, no identity question | Live CLI and IAB passed on macOS ARM and Minty at `2efd0f6` | Pending actual file |
| `booking-happy` | Eight turns: request, phone, DOB, returned option, decline, reselect, current separate consent, repeated confirmation; exactly one real POST/appointments201 | Live CLI and IAB passed on macOS ARM and Minty at `2efd0f6` | Pending actual file |
| `failure-no-match` | Three turns, no matching record, truthful next step and no queued handoff | Live CLI and IAB passed on macOS ARM and Minty at `2efd0f6` | Pending actual file |
| Service-recorded handoff | Deferred optional capability; do not show or claim delivery | Not implemented | No take required |

Original destination:

`/Volumes/Seagate Backup Plus Drive/nxus-media-studio/source-media/oscar-poc-engineering-review/assignment-captures/mvp/20261009/`

Name each take `OSCAR__mvp__<scenario>__<commit8>__T01.<ext>`; increment the take number and **never overwrite**. Media owns catalogs, hashes, normalization and derivative files. Preserve native originals. No usable lane recording currently exists; empty metadata below is intentionally incomplete.

| Metadata for each actual take | Value to record after capture |
| --- | --- |
| Actual absolute file path / format | Pending |
| Lane / repository | `mvp` / `/Users/ken/codeRepos/ochsner-scheduling-mvp` |
| Actual source commit / scenario / take | Pending; resolve source commit at recording time |
| UI URL / API port | `http://127.0.0.1:28180` / 4010, verify against running owned processes |
| Capture timestamp / timezone | Pending; record America/Chicago |
| Observed outcome / limitations | Pending; report failures truthfully |
| Reset command and resulting state | Pending actual reset; procedure below |
| Canonical notes | This file |

## Launch and reset

Follow [setup](../user/setup.md) for Python3.11+, local editable installation, key/model environment and port checks. No Bitwarden dependency is required by a reviewer. Never put credentials in footage, arguments or files. API and assistant state belong to their respective owned processes.

```sh
.venv/bin/python vendor/scheduling-reference/mock-api/server.py --port 4010
.venv/bin/python -m scheduling_assistant --model gpt-5.4-mini \
  --api-base-url http://127.0.0.1:4010
.venv/bin/marimo run apps/scheduling_app.py --headless \
  --host 127.0.0.1 --port 28180
```

Use separate terminals. The UI launch environment requires `SCHEDULING_MODEL=gpt-5.4-mini`, `OPENAI_API_KEY` and optionally `SCHEDULING_API_URL=http://127.0.0.1:4010`. Open the printed loopback UI URL in controlled IAB; headless launch opens no browser automatically.

Before a fresh happy take, stop **only the owned API process** with Ctrl-C in its terminal and rerun its command to restore synthetic bookings. Use the UI **Reset conversation** button or CLI `reset` to clear identity, proposals and displayed history. An unknown-write guard survives conversation reset; process restart is not reconciliation. If an outcome is unknown, verify through clinic scheduling staff before retrying. Never kill an unrelated listener or record a reset as proof a previous write failed. Record the actual resulting state in the take metadata.

## Limits and ending

Current-turn synthetic text goes to OpenAI; scheduling facts/effects come from the supplied local service. Matching is not authentication, dates use the service's supplied offset, and all appointments are synthetic. State/idempotency are process-local, uncertain writes require external reconciliation, and lookup/recorded handoff/medical advice/production controls are outside delivered scope. Diagnostics exclude raw identity/prompt/keys; displayed transcripts still need synthetic-only capture discipline.

Processing indicators and measured elapsed times exist; no universal 400 ms or completion-time claim is established. Live browser qualification and successful tests do not prove accessibility conformance or production readiness. Public publication/submission and assignment timing remain Operator-owned. Optional post-MVP visual refinement is deferred; preserve the working approved sponsor assets and consent controls. The [teammate synonym exercise](as-built/code-walkthrough.md#small-teammate-change-a-clear-specialty-synonym) offers a small tests-first review discussion. [Next steps](../product/next-steps.md) retains remaining work.


Post-three-hour update: actualCLI provider/booking/no-match qualified on bothhosts at3a3091c; RC-1 coveragegap resolvedforRC-2. Applicatione0996c1. RecordingstillOFF/nofootage. ExclusiveSMcapture slot andnative recorderremainrequired.
