# UI assets and familiar interaction

Updated: not yet populated. No sponsor kit or reuse permission is assumed.

| Asset / local path | Source and date | Intended use / alt text | License or approved audience | Status |
| --- | --- | --- | --- | --- |
| Pending selection | Pending | Pending | Pending | Scaffold only |

Use `assets/ui/branding/`, `images/`, `icons/` and `themes/` for small runtime assets. Keep video recordings elsewhere. Intake may describe assets or reference their paths/URLs; `--input` accepts intake documents, **not binary asset uploads**. Bootstrap exports the Template's existing `assets/ui/` files; it does not automatically download references or copy files mentioned in intake. The project owner adopts permitted assets during normal Plan/Tasks/Implement work.

Supplied assignment guidance takes precedence. If missing, research the sponsor's public colors, logos and interaction conventions only as useful; record observations as observations, not an approved brand kit. Ask whether sponsor, platform or incumbent-product UI conventions should guide the design. A coherent familiar workflow is more valuable than copying a screen. Missing branding normally uses a neutral fallback rather than blocking the MVP; an explicitly required branding conflict must be surfaced, not silently waived.

Use local, reviewed assets rather than tracking scripts or hotlinks. Check image/SVG content before adoption; preserve third-party attribution and authorized scope. Prefer system fonts unless a permitted font package is needed. Test keyboard/focus, contrast, readable labels and meaningful status/error feedback in the actual UI.[^accessibility]

Research, asset selection and documentation may overlap implementation; this index is not a new review gate. Link the actual theme/UI files from the [walkthrough](as-built/code-walkthrough.md), [architecture](as-built/architecture.md) and [video notes](video-notes.md).

[^accessibility]: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/). Reviewed 2026-10-07. Check keyboard/focus, contrast, readable labels and meaningful error/status feedback. Limit: Targeted PoC checks do not establish full conformance.
