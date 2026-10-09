# Milestones and optional UX refinement

Updated: 2026-10-08. Tags below are annotated and immutable; no assigned-window compliance or product readiness is implied.

| Tag | Source commit | Purpose / timing | Relevant docs or demo |
| --- | --- | --- | --- |
| `poc/scaffold` | `15a1e17` | Isolated scaffold backup, privately pushed; product unimplemented | Native spec/plan work continues in `specs/001-scheduling-assistant/` |
| `poc/planned` | `cc4535d` | Cumulative planning and all Analyze findings resolved; privately pushed | `specs/001-scheduling-assistant/` |

Create **annotated, immutable tags** for useful reviewed milestones—not each tool call. Suggested names: `poc/scaffold`, `poc/planned`, `poc/mvp`, `poc/ux-01-before`, `poc/ux-01-after`, `poc/submitted`. Use `poc/budget-baseline` only when the Operator directs capture of an actual agreed work-window baseline. Names are suggestions, not mandatory gates; tags do not confer release/publication authority.[^tagging]

After committing the intended source and verifying the tag is unused:

```sh
git tag -a poc/mvp -m "Working MVP checkpoint"
git rev-parse 'poc/mvp^{commit}'
# Only with push authority to the confirmed remote:
git push origin refs/tags/poc/mvp
```

Record the tag, resolved commit and purpose here in the next documentation commit; do not move a tag to include its own record. Use a new numbered tag for a later checkpoint. Never force-update tags or push all unrelated tags. See [Git setup](git-setup.md) for remote/commit cadence.

## Optional refinement

During Spec-Kit Tasks, consider an **optional post-MVP** task for a bounded UI/UX flow/polish pass. It cannot delay a working required slice, weaken acceptance, or substitute for core correctness. Follow the Operator's scope and timing decisions; agents must not silently stop or shrink work based on estimated elapsed time.

If selected, retain the working baseline with a pre-refinement tag, make the focused changes, test affected behavior, and tag the post-refinement result. Document the user benefit/trade-off in the existing decisions/next-steps files. Comparable synthetic-data screenshots or short clips may help the review; use the same scenario/view and disclose any separately permitted later work. If not selected, put a brief deferred item in next steps—no unfinished mandatory gate.

Link relevant tags from as-built docs and video notes instead of duplicating this table. Budget compliance and permission for supplemental work remain Operator decisions; never imply all versions were built within an agreed time window.

## Optional adversarial review

Consider one near-final or explicitly deferred task to populate the [review report](reviews/adversarial-review.md). Reuse a sufficient existing independent review. Preserve the source commit reviewed; commit sanitized findings and useful synthetic regressions. A suggested immutable tag is `poc/review-01`; record its source here and push that named tag only under existing destination/privacy authority. No raw consultation transcript, new mandatory gate or extra publication grant.

[^tagging]: [Git: tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging). Reviewed 2026-10-07. Use annotated tags for meaningful source checkpoints and explicitly push selected tags. Limit: A checkpoint is not release/publication authority or a budget-compliance claim.

## 2026-10-09 two-hour progress checkpoint

Immutable annotated `poc/checkpoint-2h-20261009` points to `a1af7ca24fd555bdfc5de669c82ab93c1dd15fd9`. Actual clean-tree capture00:42:37.999130CDT; target00:41:01CDT;97seconds late. Existing private origin main and peeled tag were verified at that exact SHA after non-force pushes. This is progress, not completion: local live CLI/IAB journeys passed; fresh-host, final documentation and video work remained. All writers were quiescent; implementation resumed immediately.


## 2026-10-09 three-hour checkpoint and RCs

Immutable annotated `poc/checkpoint-3h-20261009` and `RC-1` resolve to `3a3091cbe49e250617741d983bf11f0c70428f21`. Three-hour actual clean capture01:41:06.357331CDT, target01:41:01CDT,5.357seconds late. All writers quiescent, clean tree; non-force private main and peeled checkpoint verified. RC-1 created06:41:48.936695UTC, explicitly Operator-approved without latestCLIcoverage; remote peeledRC-1 verified. Neither tag implies finishedvideo/publication/productionreadiness.

Immediately resumed approved work. Post-checkpoint genuineCLI flows passed on both clean hosts at3a3091c, resolving RC-1's knowncoveragegap. RC-2 will annotate the following documentation-only evidence commit; its exactSHA/timestamp live in the immutable tag annotation, avoiding a self-referential commit record. Application bytes remain e0996c1. See [verification](scheduling-verification.md).


## Approved shared Persona milestones

`poc/personas-introduced-v1`→667a08b685a3667c8f0e3101163762b0fd446645, remotelypeeledverified; exactfourpins/threeancestors/cards/stories, no productimpactincluded. Application8716779 thenrepairs Morgan-Rae supportcertainty/context withtests-firstregressions; Ellie/Samchecks verifyexistingbehavior. Bothfreshhosts118tests+demos and actualaffectedCLI/IAB checks passed. `poc/personas-impact-v1` and nextunusedRC-3 will annotate the finaldocs/evidencecommit with unchanged8716779 applicationbytes; exactSHA/actualtime in immutableannotations. No documentation-only impactclaim; videoONHOLD.
