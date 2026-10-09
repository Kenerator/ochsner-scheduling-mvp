# PoC work increment

Updated 2026-10-09. Formal sprint dates are deferred; the selected increment is the approved scheduling MVP. Operator owns effort-window compliance and trade-offs.

Goal: genuine AI provider lookup, exact confirmed booking and truthful failure assistance in both CLI and Marimo. Accepted behavior: [spec](../../specs/001-scheduling-assistant/spec.md). Design/dependencies: [plan](../../specs/001-scheduling-assistant/plan.md). Detailed work and completion: [native tasks](../../specs/001-scheduling-assistant/tasks.md).

Execute disjoint component work in parallel after stable contracts and failing behavior tests; integrate before dependent outcome checks. The shared controller owns effects. Thin CLI/UI owners cannot change identity or consent policy independently. As-built walkthrough, architecture and video documentation follow stable implemented components.

The current increment includes supplied HTTP success/failure demos, genuine live AI qualification, controlled in-app browser checks, fresh private GitHub-clone setup on both approved hosts, and honest recording/handoff evidence. Passing unit tests does not complete those checks. Shared Persona pins are adopted; actual user validation remains pending; optional lookup/handoff and production controls are deferred. No extra engine or admin console is added.

[Backlog](backlog.md), [roadmap](roadmap.md) and [next steps](next-steps.md) keep priorities and handoff concise; they are not duplicate completion ledgers.
