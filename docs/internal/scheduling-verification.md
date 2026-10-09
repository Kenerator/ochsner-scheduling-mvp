# Scheduling verification

Updated 2026-10-09. Reviewed application source: `e0996c1c8a438b6b6bfeff5283b5b3b02ddd8e69`; documentation finalization follows separately. Native [tasks](../../specs/001-scheduling-assistant/tasks.md) own progress. Synthetic fixtures only; no production, assigned-window or finished-video claim.

## Automated and fresh-clone verification

Fresh authenticated private GitHub clones were installed using declared project-local dependencies on Mac ARM (Python3.12.12) and Minty Linux x86_64 (Python3.12.3, glibc2.39). Marimo is pinned0.25.0. Both dependency checks passed. At source e0996c1, `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` passed114 tests (Mac1.315s, Minty4.232s). Strict Marimo check passed. Clean clone roots were `/private/tmp/ochsner-mvp-mac-clone-20261009.RFZ21F/repo` and `/home/ken/.cache/poc-mvp-qualification-20261009.m89xaT/repo`. Reviewer setup uses ordinary GitHub access/environment credentials, with no Bitwarden dependency. An existing host SSH alias was used for authenticated qualification; no host trust or global tooling changes.

Both `scripts/demo_scheduling.py --scenario success` and `--scenario failure` passed on both hosts at e0996c1. These use an explicitly **simulated interpreter and actual supplied HTTP** on fresh owned ephemeral services. Success: seven turns, providers/search/availability200 and exactly one POST201, decline/reselection/separate consent/repeat protection. Failure: three turns, providers/search200, zero availability/POST, truthful clinic guidance. These runs do not qualify live AI.

## Genuine model and interfaces

Explicit model `gpt-5.4-mini`, direct Responses strict extraction, authorized process-local credentials. No key/raw transcript retained in this record. Sequential single-user observations, no load benchmark.

At `2efd0f6`, both fresh-host actual CLI and IAB/Marimo completed provider (two turns), booking (eight turns, separate phone/DOB, decline/reselection/current consent/repeated yes) and no-match (three turns, one correction). Each booking had search200/availability200/exactly one POST201; no-match had two search200 and zeroPOST. Minty CLI scenario totals were3.686s/9.771s/3.892s. The supplied API audit contains only operation/status/timing, not query/body.

At `947e621`, Mac actual IAB rechecked hidden framework export menu, Send, proposal-enabled Confirm, decline-disabled Confirm, fresh selection/current confirmation, repeated yes, Reset, and no-match. Actual booking201 and no extra POST on repeat. The optional framework PNG export had stalled in IAB; HTML export downloaded successfully. The menu is hidden through Marimo's intentionally stable `notebook-actions-dropdown` CSS hook; its exports are outside the scheduling flow. No PNG success is claimed.

At e0996c1, Mac and Minty actual IAB requalified provider lookup, booking with decline/reselection/dedicated confirmation/repeat protection, reset and bounded no-match; genuine 'Book neurology' stopped with unsupported-scope/clinic guidance. An earlier live request dropped the unsupported specialty and asked for identity. The extraction prompt now explicitly preserves unsupported values and stops that intent; a red-to-green request-contract regression and the actual model retest support this fix. AI interpretation can still fail and is not deterministic authority.

The first Minty restart attempt found its old task-owned UI still listening. Its exact /proc cwd/command were verified before terminating only that process; the new e0996c1 process then passed the complete UI rehearsal. No unrelated listener was stopped.

An additional CLI rerun was initially rejected by automatic approval review; neither denied attempt ran. The Operator then directly instructed RC-1 without this coverage, post-three-hour CLI resolution and another RC. After the verified checkpoint, genuine actualCLI provider(two turns), booking(eight turns with decline/reselection/separate consent/repeat guard) and no-match(three turns) passed on both clean hosts at RC-1 source `3a3091cbe49e250617741d983bf11f0c70428f21` (application e0996c1 unchanged). Mac API audit: two providers200, search200/availability200/exactly onePOST201 for booking, two search200/zeroPOST for no-match. Minty owned ephemeral suppliedHTTP independently confirms the same operation counts/statuses; scenario totals3.133s/8.882s/2.978s. All CLI processes exited0; no credentials/transcripts persisted. This resolves the CLI coverage gap for RC-2.

## Useful feedback and completion

Single-user, one provider turn per measurement, loopback API. Automation observations include control roundtrips; stdout pipe measurement is not a terminal-paint benchmark.

| Interface/source | Useful feedback | Completion | Details |
| --- | --- | --- | --- |
| Mac CLI947e621 | Processing marker0.088ms after stdin write | next prompt1159.739ms | startup86.393ms separate; model1157.478ms; API1.953ms |
| Mac IAB947e621 | visible spinner293ms | assistant result1227ms | click-to-observation, single sample |
| Minty IAB2efd0f6, SSH loopback forward | visible spinner294ms | assistant result2253ms | single sample, remote UI |

These samples met the useful-feedback400ms target in their stated conditions; no percentile, load or general guarantee is inferred. Model transport timeout30s, service timeout5s. Diagnostics separately measure interpretation, operation and total turn using a monotonic clock, allowlisted enums/finite durations only. No raw prompts, identity, credentials or arbitrary errors are logged.

## Safety and browser evidence

Actual Mac IAB checks also covered private duplicate ZIP resolution, empty availability, advice/human/deferred-lookup guidance, real409 conflict-trap refresh with no repeated POST, and safe service-outage guidance. Dedicated confirmation is enabled only for the current proposal. Reset clears transcript; unknown-write state remains protected in actual HTTP integration and UI tests. A second tab began with independent conversation state. Keyboard Tab reached Send; blank Return showed validation without effects. Logo/blue-gold local assets and visible focus were inspected; no blanket accessibility claim.

One independent combined review found stale ZIP after changed identity, completed appointment binding after changed identity/preferences, missing UI Diagnostics and missing escalation reason codes. All four were fixed with regressions. Actual-browser disappearing controls after spinner were fixed using Marimo state self-rerun and a real callback/scheduler regression. Follow-up tests cover missing-identity-only prompts, bounded no-match searches, fresh conflict-exclusion cycles, unsupported values and prompt guidance. Actual supplied HTTP tests cover committed201 with a dropped reply: unknown remains across reset, no secondPOST. Only exact validated201 proves booked;409 requires fresh choice/consent. No recorded handoff is implemented.

## Documentation and remaining work

As-built62links and47source symbols were checked. Both Mermaid diagrams rendered as SVG in controlled IAB with pinned Mermaid11.12.0 from a disposable local review page; module/effect arrows and booking outcome paths were visually inspected. No repository/global renderer dependency was added. Screenshots are outside Git and are not continuous footage.

Recording remains OFF. No continuous video exists. [Video notes](video-notes.md) hold the test-before-video checklist; SM must assign an exclusive capture slot, and actual native recording capability must be available. Latest-source CLI coverage is resolved after direct Operator authorization, as recorded above. Named/pinned Persona validation remains pending; no console/delivery permission is implied.
