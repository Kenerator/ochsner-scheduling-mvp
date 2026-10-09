# Ochsner scheduling MVP

A local AI scheduling assistant for synthetic provider lookup and appointment booking. A shared Python controller verifies patient matches, displays returned slots and requires a separate confirmation before booking. A CLI and Marimo conversation form use that same controller and the supplied independent reference API.

Requires Python **3.11+**, an OpenAI API key in the process environment and an explicitly selected Responses model. Marimo is pinned in `pyproject.toml`; no database, rules engine or Bitwarden runtime dependency is required. Use synthetic data only. This is an internal proof of concept; identity matching is not authentication.

## Start and verify

Follow [setup](docs/user/setup.md) to install locally, check ports and start the loopback API and either interface. [Usage and recovery](docs/user/usage.md) gives the synthetic multi-turn flows and explains confirmation, reset and uncertain outcomes.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario success
PYTHONPATH=src .venv/bin/python scripts/demo_scheduling.py --scenario failure
```

The demos run the actual supplied HTTP service on isolated ephemeral ports with a **scripted interpreter**. They make no live AI claim. Live CLI/UI qualification, fresh-host setup and capture evidence are recorded separately in [video notes](docs/internal/video-notes.md) and the authoritative [tasks](specs/001-scheduling-assistant/tasks.md); those checks are still in progress as of 2026-10-09.

## Document index

- Requirements and execution: [spec](specs/001-scheduling-assistant/spec.md), [plan](specs/001-scheduling-assistant/plan.md), [tasks](specs/001-scheduling-assistant/tasks.md), [validation guide](specs/001-scheduling-assistant/quickstart.md).
- Use: [setup](docs/user/setup.md), [usage and limitations](docs/user/usage.md), [synthetic reference fixtures](vendor/scheduling-reference/data/README.md).
- Design: [decisions](docs/product/decisions.md), [code walkthrough](docs/internal/as-built/code-walkthrough.md), [architecture](docs/internal/as-built/architecture.md), [UI assets](docs/internal/ui-assets.md).
- Priorities: [backlog](docs/product/backlog.md), [roadmap](docs/product/roadmap.md), [work increment](docs/product/sprint-planning.md), [next steps](docs/product/next-steps.md), [pending Personas](docs/product/personas.md).
- Review and demonstration: [video notes](docs/internal/video-notes.md), [milestones](docs/internal/milestones.md), [credential guard](docs/internal/security.md), [optional adversarial review](docs/internal/reviews/adversarial-review.md).

Existing appointment lookup and recorded handoff are deferred. Assistance means contacting clinic scheduling staff; no transfer is claimed. State and the unknown-write guard are process-local, with no production durability or automatic reconciliation. Approved local branding is for internal review; external publication requires separate authorization.
