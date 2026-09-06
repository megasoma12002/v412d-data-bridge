# Coding Standards — Coverage Map

Date: 2026-09-06  
Question: "整個專案都 code review 並套用準則修正嗎？"  
Short answer: **Previously no (E45 path only). Now yes for actionable `scripts/` violations.**  
Standards: `research/ops/CODING_STANDARDS.md` · E45 landmines: `research/ops/E45_PAPER_LANDMINE_CODE_REVIEW.md`

## What "whole project" means here

| Layer | Covered? | Notes |
|---|---|---|
| Live path (`e21_*`, Soft-Frozen base, ops alerts/pack) | **Yes** | Single-source / fail-closed from #55/#56; re-checked |
| Shared sim (`e50_early_stack_combined_nav`) | **Yes** | None-safe deltas; first-class cost/sleeve kwargs |
| E45 paper / observe | **Yes** | Harness, claim labels, book IDs, no monkeypatches |
| Active research (`e22_*`, `mdd_*`, gap/FINCAP screens) | **Yes** | Metric `or 0` cleared; Soft-Frozen JSON imports `SOFT_FROZEN_FIN_CLIP` |
| Archived Stage-8 / E50-A3-R1 OOF scripts | **Yes (utility / sort keys)** | `utility_score` / `abs_mdd`; not a full grid rewrite |
| Docs / Markdown KEEP mentioning `[0.50, 0.95]` | **Allowed** | Prose KEEP ≠ second clip source |
| `repro/` blobs | **Hygiene only** | gitignore bulky fills/NAV; not re-simmed |

## This sweep

1. Project scan of `scripts/*.py` against landmine patterns  
2. Helpers: `metric_delta`, `utility_score`, `fmt_pct` (+ existing delta/abs helpers)  
3. Soft-Frozen list export: `e16_soft_frozen_base.SOFT_FROZEN_FIN_CLIP`  
4. Residual CAGR/MDD `or 0` emitters cleared under `scripts/`  
5. Hygiene gates (both **PASS**):
   - `python3 scripts/check_e45_paper_hygiene.py`
   - `python3 scripts/check_project_coding_hygiene.py`

## Explicitly not claimed

- Did **not** re-run every historical research grid or rewrite every prose KEEP line  
- Did **not** Soft-Frozen flip / live stitch / invent −13.16% replacement  
- Did **not** auto-open new observe sleeves  

## Re-check

```bash
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
```

## Label

`CODING_STANDARDS_COVERAGE_2026-09-06__PROJECT_SCRIPTS_PASS`

## 2026-09-06 debt closure

- E45 regenerators must import `e45_paper_harness`; local `load_market`/`window_stats`/`blend` forks fail hygiene.
- Live market path gate uses resolve equality; FIN/TEL single-sourced from Soft-Frozen base.
- Month-end pack default behavior unchanged; opt-in `--fail-on-critical`.

## 2026-09-06 landmine follow-up

- Research batches (`*research_batch*` / `*_batch.py`) are regenerators (must import harness).
- Harness `__all__` must match defined names (hygiene fail-closed).
- Review: `PROJECT_LANDMINE_CODEREVIEW_2026-09-06.md`.
