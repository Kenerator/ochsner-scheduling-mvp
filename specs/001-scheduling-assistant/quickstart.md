# Quickstart validation guide

Designed 2026-10-08. **Future implementation guide:** the scheduling package, app, vendor copy and demo script below do not exist yet. Commands define the planned acceptance surface; Plan has not installed dependencies, started services or qualified live AI. Generic `poc_demo` is not scheduling evidence. Contracts: [interaction](contracts/interaction.md), [service](contracts/scheduling-service.md), [data model](data-model.md).

## Prerequisites and setup after implementation

Local terminal/browser, compatible Python 3.11+, synthetic supplied fixtures, approved internal-review sponsor assets (now present; UI integration unverified), project-local dependencies. Live qualification additionally needs an authorized runtime OPENAI_API_KEY already in the environment and explicit model selection; do not print keys or put them in command arguments/source. This planning invocation grants no credential access or model execution.

From repository root, verify `python3 --version` is >=3.11; if not, use an explicit compatible executable for venv creation. Then:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Implementation declares/pins reviewed Marimo dependency and preserves bootstrap tooling. Check listeners before binding4010/28180 (`lsof -nP -iTCP:4010 -sTCP:LISTEN` and corresponding28180); occupied ports are a setup error, not permission to terminate unrelated services.

Start supplied independently vendored server in terminal A:

```sh
.venv/bin/python vendor/scheduling-reference/mock-api/server.py --port 4010
```

Expected loopback4010 startup; source/provenance recorded in vendor index. No database/install for server. Safe provider smoke in terminal B:

```sh
curl 'http://127.0.0.1:4010/providers?specialty=primary_care&location=downtown'
```

Expect returned providers array. Runtime assistant must call HTTP; do not read fixtures to answer users. Mock request audit independently confirms actual operation/status and excludes query/body. Keep records sanitized.

## Automated and deterministic validation

Run tests first during implementation, demonstrate meaningful red then green for changed behavior. Final required command under a verified compatible interpreter:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Project-local equivalent: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`. Tests cover provider-only no identity, unique/duplicate/no-match identity, private ZIP zero/multiple/unique, supported filters/date boundaries, returned-only selection, absent/declined/ambiguous/changed consent, repeated confirmation, no advice, malformed reads/writes,409,503, transport ambiguity, reset unknown guard, privacy and reactive event replay. Assert outbound operation count and exact proposal/result bindings, not just message wording.

With fresh independent mock state:

```sh
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario success
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario failure
```

Success performs provider lookup then unique synthetic booking, displays returned slot, confirms in a separate turn and reports valid201 appointment; exactly one POST. Failure uses no-match identity, no patient details/availability/booking, and reason-specific guidance to contact clinic scheduling staff. These use a labeled scripted interpreter, not live AI. Restart only the owned mock between state-sensitive runs; repeat confirmation after success must not replay booking.

## Live CLI qualification

In authorized runtime with key already configured:

```sh
PYTHONPATH=src .venv/bin/python -m scheduling_assistant --model gpt-5.4-mini
```

Use synthetic turns:

1. “Which primary care providers are downtown?” Or omit location, answer follow-up, verify context retained and no identity questions.
2. “I want to book primary care downtown.” Supply phone `555-0101`, DOB `1985-04-12` when asked. Select a currently displayed non-conflict slot by ordinal; do not hardcode fixture dates. Verify full returned proposal including offset. Decline once to prove no POST, reselect and confirm on a later turn. Expect scheduled appointment with returned ID and one POST. Repeat confirmation; zero extra POST.
3. Reset and request booking with phone `555-9999`, DOB `1990-01-01`; provide correction or request help. Expect truthful no-match assistance and zero patient-specific calls/POST.

Record sanitized scenario, model, environment, date, turn count, API operation/status counts and measured latency; label live vs scripted evidence. Do not save raw sensitive transcripts or claim shared model availability proves these flows.

## Live Marimo qualification

Set explicit nonsecret `SCHEDULING_MODEL=gpt-5.4-mini` in the authorized runtime; same existing key environment. Terminal C:

```sh
.venv/bin/marimo run apps/scheduling_app.py --host 127.0.0.1 --port 28180
```

Open http://127.0.0.1:28180. Repeat provider, booking and no-match multi-turn journeys above. Verify AI disclosure, retained answers, approved logo/colors, escaped text, labels, keyboard/focus and useful status. Submit/re-render/double-click must not duplicate turns or POST. A changed proposal invalidates old confirmation. Check independent browser sessions do not share private conversation state. Record actual browser review separately from automated parity tests; no blanket WCAG claim.

## Failure/recovery boundaries

- Duplicate phone `555-0130`, DOB `1978-09-22`: private ZIP clarification; `70115` or `70005` yields a unique candidate. Never show candidate details; wrong/ambiguous ZIP stops patient actions.
- Dermatology/lakeside: empty availability, offer supported changed search or human assistance.
- Select service-returned conflict slot:409, fresh alternatives without repeated trap in current recovery, fresh choice/confirmation, no booked message.
- Start assistant with explicit test `--scenario api_failure`: supplied503, reason-specific assistance, no fictitious queued handoff.
- Advice, human, existing lookup, reschedule/cancel, unsupported appointment type: no clinical answer or unsupported operation; actual assistance guidance only.
- Inject timeout-after-write and malformed/mismatched201 in transport tests: unknown result, no blind retry, reset cannot remove blocking warning. Optional lookup is not an automatic reconciliation workaround.

Reset clears conversation/identity/proposal, not mock bookings or unknown outcome truth. Restarting mock resets synthetic server state; it is not evidence a previous write failed. Process restart loses in-memory safeguards, so clinic verification is required after uncertainty before attempting another booking.

## Completion evidence after integration

Verify from fresh authenticated private GitHub clones on both macOS ARM and Minty Linux x86_64: declare prerequisites, install locally, start supplied mock, run tests and both demos, qualify live CLI/UI flows, check branding and sanitized diagnostics, record useful-feedback/completion timing with single-user workload and unmet target impact. No benchmark claim without measurement.

Finalize dated as-built architecture/walkthrough from actual source/tests with reviewed revision and checked navigation/diagrams. Update README document index, setup/recovery, video notes and <=5-minute provider/booking/failure/tradeoff script; include small teammate exercise (e.g. add a supported synonym with tests while preserving consent). Native tasks own status; link remaining gaps in next steps. No external submission, video publication, push, deployment or assigned-window claim is authorized/proven by these checks.
