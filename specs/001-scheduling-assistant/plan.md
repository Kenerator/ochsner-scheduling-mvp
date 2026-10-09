# Implementation Plan: AI Appointment Scheduling Assistant

**Branch**: native feature label `001-scheduling-assistant`; actual local Git branch `main` (Git extension disabled, no branch created). **Date**: 2026-10-08. **Spec**: [spec.md](spec.md).

**Input**: `specs/001-scheduling-assistant/spec.md`, unchanged dependency verified against the supplied contract. Approved delivery constraints: [Q1](scope-decisions.md). This stage ends at Phase 1; no tasks or scheduling implementation are represented as completed.

## Summary

Build genuine multi-turn AI provider discovery and confirmed booking in a terminal and thin Marimo form/transcript. A reusable Python core owns identity, returned facts, exact consent, booking and recovery. The model extracts intent/answers; the supplied independent API owns scheduling data. Only validated HTTP201 evidence supports booked output. Existing appointment lookup and recorded handoff remain deferred; assistance is truthful guidance to clinic scheduling staff. Research and alternatives: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+; verify executable before setup/UAT.

**Primary Dependencies**: standard-library dataclasses, enum, json, urllib.request, argparse and unittest; Marimo reviewed candidate 0.25.0 for required UI. Direct HTTPS Responses API adapter with explicit model; no OpenAI SDK or rules engine. Preserve bootstrap dependencies/configuration.

**Storage**: session-local conversation and displayed facts; process-local action ledger/unknown-effect guard. Supplied server uses in-memory bookings. No database, durable authentication or cross-session replay guarantee.

**Testing**: unittest tests first, injected interpreter/gateway, actual supplied-server HTTP integration, CLI/UI parity and browser checks, separate live AI qualification. Required command `PYTHONPATH=src python3 -m unittest discover -s tests -v` plus success/failure demos; use a verified compatible python3 or explicit venv equivalent.

**Target Platform**: local Python environment and browser; UI 127.0.0.1:28180, independent supplied API 127.0.0.1:4010. Internal review only.

**Project Type**: reusable library with CLI and thin Marimo adapter, separate supplied service.

**Performance Goals**: useful processing feedback target 400 ms where feasible; record completion and service/model elapsed times separately with scenario/environment/load. Start with single-user sequential turns, finite 5-second scheduling and 30-second model timeouts, no automatic retries. These are design limits, not measured guarantees; timeout recovery never replays an uncertain POST.

**Constraints**: synthetic inputs only; no raw sensitive logs; OPENAI_API_KEY from environment, required explicit model (`gpt-5.4-mini` qualification target); no credential store dependency. Approved local sponsor assets required; SVG/CSS and provenance index appeared during planning and are present at final inspection, unmodified by this stage. No optional integrations or production/authentication claim. Operator owns assignment window; MLX owns remote provisioning.

**Scale/Scope**: one candidate, two interfaces, provider lookup and booking plus all reachable safety failures. primary_care/dermatology and downtown/uptown/lakeside per API. Persona selection/validation remains explicitly pending for primary user and Support/Admin.

## Constitution Check

Gate reviewed before Phase 0 and again after Phase 1 against Constitution 0.2.1. PASS for this design, with disclosed implementation dependencies; no exemption or amendment.

| Principle | Pre-research gate | Post-design evidence |
| --- | --- | --- |
| I Empathy | Spec maps US1–5 and pending Personas | Shared follow-ups, private ZIP and US4 diagnostics; validate Personas later, no invented constraints |
| II Predictability | Exact consent and truthful recovery required | [state model](data-model.md) and [interaction contract](contracts/interaction.md) invalidate changed consent; reset retains unknown warning |
| III Responsiveness | 400 ms feedback target without unsupported claims | Both adapters show processing, measure elapsed phases and report unmet targets |
| IV Small core | Reusable logic, effects in adapters | Injected interpretation/gateway, common controller; no extra backend/database/engine |
| V Verification | Behavior tests precede code | [quickstart](quickstart.md) separates scripted tests, supplied API demos and live UI/CLI evidence |
| VI Safety | Synthetic data and truthful effects | Strict service validation, safe diagnostics, no new external grants; [service contract](contracts/scheduling-service.md) |
| VII Documentation | User/support setup and as-built needed | Near-final docs after stable implementation, reviewed revision/date and navigation/diagram checks |
| VIII Governance | Native artifacts own requirements/status | Tasks stage owns progress; disjoint parallel work with prerequisites; linked short handoff |

Asset presence is confirmed but UI use/verification and Personas are not completed, live model access is developer-reported only, and no performance is verified. None requires altering the Constitution or blocking design. FR-017 remains required; verify local assets and their integration during implementation.

## Project Structure

All paths below are planned unless already existing; preserve managed/template source.

```text
specs/001-scheduling-assistant/
├── spec.md
├── scope-decisions.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interaction.md
    └── scheduling-service.md

src/scheduling_assistant/
├── __init__.py
├── __main__.py           # CLI entry
├── domain.py             # typed snapshots, state and transitions
├── core.py               # safety guards and response facts
├── session.py            # serial turn/effect orchestration
├── interpretation.py     # constrained interpretation protocol
├── scheduling_api.py     # supplied service HTTP boundary
├── openai_adapter.py     # structured Responses interpretation
└── diagnostics.py        # allowlisted non-sensitive events
apps/scheduling_app.py    # thin Marimo form/transcript
vendor/scheduling-reference/
├── PROVENANCE.md
├── openapi/scheduling-api.yaml
├── mock-api/server.py
├── mock-api/README.md
└── data/                 # four supplied fixtures plus guide
assets/ui/branding/       # existing approved local logo
assets/ui/themes/         # existing local approved theme
scripts/demo_scheduling.py
tests/
├── test_scheduling_core.py
├── test_scheduling_session.py
├── test_scheduling_api.py
├── test_scheduling_ai.py
├── test_scheduling_interfaces.py
└── test_scheduling_integration.py
```

**Structure Decision**: new small application package alongside untouched starter; selective private vendor copy of public contract, supplied server and synthetic fixtures with source paths/checksums/provenance. Exclude original intake metadata and unrelated attachments. Vendor copy is for authorized internal local use, not a publication grant. `tasks.md` is generated by the next native Tasks stage, not this command.

## Phase 0 — Research result

[Research](research.md) resolves design choices: typed core, strict HTTP response validation, exact proposal ledger, direct structured AI interpretation, Marimo submitted events and safe observability. Independent researchers inspected service and UI boundaries without competing writes. Runtime installation and live flow qualification remain future verification, not unresolved scope decisions.

## Phase 1 — Design result

[Data model](data-model.md) defines private identity and proposal state. [Interaction](contracts/interaction.md) defines CLI/UI/config/interpretation boundaries. [Service contract](contracts/scheduling-service.md) maps actual wire fields, statuses and uncertainty. [Quickstart](quickstart.md) defines future runnable verification and expected outcomes without implementation bodies.

Deterministic messages render validated returned facts. The AI never renders authoritative booking results or supplies patient/slot IDs. Confirmation is recognized from the actual subsequent user turn or dedicated proposal-bound control, rather than an AI-provided authorization flag. Unsupported/advice/human intent immediately stops scheduling; model refusal/failure cannot continue a booking. One serialized controller owns effects for each session. Process-level unknown-effect records survive UI/conversation reset and block new booking attempts until externally reconciled; no MVP automatic reconciliation capability is invented.

## Delivery sequencing for Tasks

1. Write domain/safety behavior tests before implementation, including negative/privacy/replay/unknown cases. Stabilize typed protocols and safety core first.
2. After protocols, disjoint API adapter and AI adapter test/code lanes may run in parallel with clear file owners; test writers precede their implementations. Selectively vendor supplied service/fixtures in a separate lane. Neither model nor fixtures replace server integration.
3. Integrate session controller and confirm combined behavior before CLI/UI lanes. CLI and Marimo disjoint files may proceed in parallel against stable controller; serial effect ownership remains shared design.
4. Run supplied-server demos and meaningful integration; live synthetic model flows in both interfaces require execution qualification and authorized runtime environment. Adopt permitted assets and check keyboard/focus/contrast/status/escaped content. Do not silently substitute optional UI for required lane.
5. Near-final tasks populate `docs/internal/as-built/code-walkthrough.md` and `architecture.md` from actual source/tests after relevant components stabilize; draft independent files in parallel, integrate and verify links/diagrams, date and reviewed source revision before completion. Update actual-code video notes/demo script (<=5 minutes), fresh private GitHub-clone setup on macOS ARM and Minty Linux x86_64, plus a small teammate modification exercise. Keep README short linked index.
6. Populate or explicitly defer backlog/roadmap/sprint-planning; native tasks own progress. Update short next steps honestly. Consider one optional sanitized adversarial review; adequate existing independent review may suffice. Milestone tags/commits only under applicable local authorization/guard; push/publication needs separate current grant. Optional UI refinement must not block required slice.

## Complexity Tracking

No Constitution violations requiring justification. Prototype limitations: process-local state, synthetic identity rather than authentication, fixed mock time offset, no durable idempotency or concurrent production booking guarantee, no automatic unknown-write reconciliation, unresolved Personas and unverified local asset/UI integration integration. Record actual evidence/debt at implementation handoff without shrinking accepted scope.

## Analyze remediation — 2026-10-08

All findings fixed under standing fix-all direction: T059 now requires fresh authenticated private GitHub clones on both approved hosts; T056 preserves bounded existing process-local credential qualification authority without reviewer Bitwarden dependency; T067 records current verified private remote/non-force milestone push authority. No public publication or credential-change grant is added. All17 functional requirements remain covered.
