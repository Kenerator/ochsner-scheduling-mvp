# Approved Q1 delivery constraints

Updated: 2026-10-08. Source: explicit developer answer supplied with Specify run e574f78f. This record preserves delivery constraints for planning; it is not implementation or live qualification evidence, and it does not expand stage authorization.

- Existing approved common contract gives `assignment.md`, `policies.md` and OpenAPI precedence. Existing appointment lookup is optional/deferred in the MVP; retain phone + DOB matching and private ZIP disambiguation within booking. Offer actual human-assistance guidance for unsupported lookup; never claim delivery or staff engagement without evidence.
- Required MVP lane: genuine AI multi-turn CLI plus thin Marimo form/transcript on loopback port 28180, using the supplied independent mock on port 4010. Share the reusable core and policy rules across thin adapters. A scripted fixture flow does not qualify live AI behavior.
- Use API-returned slots and current exact patient-bound consent. Only a valid `201` appointment with returned `status: scheduled`, matching the proposal, establishes booked success. `409` requires refreshed availability, new choice and fresh confirmation. Unknown POST outcomes prohibit blind retry.
- Use standard environment `OPENAI_API_KEY` and a configurable explicit model. Developer reports `gpt-5.4-mini` live availability as shared-qualified; Specify has not verified availability or made a model call. MVP live flow qualification remains required. Do not log raw sensitive transcripts, identifying parameters, patient responses or secrets.
- Use approved sponsor theme/logo local assets; retain their source/use index. No specific asset bytes or paths were supplied by this answer; adopt permitted assets in implementation and report any actual conflict visibly.
- Tests first. Plan near-final tasks to populate and verify actual-code architecture/walkthrough and video notes, after relevant components stabilize and integration succeeds. Preserve synthetic fixtures. Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` and success/failure demos before claiming implementation completion.
- Already authorized local implementation needs no extra approval, but this invocation executes Specify only. No remote provisioning, publication, deployment, credential access or permission bypass is granted here; remote provisioning is centrally owned by MLX.

Canonical behavior and acceptance: [spec.md](spec.md). Future implementation design belongs in `plan.md`, and progress belongs in `tasks.md` when those stages run.
