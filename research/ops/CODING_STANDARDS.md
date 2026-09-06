# Coding Standards (project engineering)

Date: 2026-09-06  
Status: **BINDING for new code** — Soft-Frozen Financial clip **[0.50, 0.95] KEEP**  
Companion: `CURSOR_RULES.md` · `research/ops/LIVE_CLAIM_TARGET_POLICY.md` · `research/ops/ARTIFACT_RETENTION.md` · `research/ops/E45_PAPER_LANDMINE_CODE_REVIEW.md`

Derived from E45 paper landmines and prior code-review rounds (#55 Soft-Frozen single-source / Exact T+1 / None-safe scorers; #56 live QC fail-closed). Engineering standards only — not a Soft-Frozen flip or stitch license.

## 1. Fail closed on live / Soft-Frozen paths

- Missing data, missing par, same-bar fill, or non-canonical path → **hard fail**, never silent coerce.
- Live QC (`scripts/e21_qc.py`) refuses non-canonical state dirs unless explicitly opted in.
- Prefer `raise` / non-zero exit over “best effort” on cutover-adjacent code.

## 2. `None` is not `0`

- Never use `x or 0` / `x or 9` when `0.0` is a valid MDD/CAGR.
- Use `scripts/research_metric_helpers.py`: `mdd_delta_pp` / `cagr_delta_pp`.
- Hot-path scorers (dual-paper, OOF, monitors) must stay None-safe.

## 3. Soft-Frozen is single-source

- Live Financial clip **[0.50, 0.95]** lives in `scripts/e16_soft_frozen_base.py`.
- JSON / machine fields must import `SOFT_FROZEN_FIN_CLIP` (or `SOFT_FROZEN_FIN_LO/HI`) — do not re-type `[0.50, 0.95]` as data.
- Markdown / log **KEEP** statements may still *mention* the band; that is prose, not a second source.
- Challenger clips stay in challenger modules only.

## 4. Claim honesty (labels)

- Emit claim status from `e45_crisis_core.CLAIMED_MDD_STATUS` (`RETIRED_HISTORICAL_NARRATIVE`).
- **Banned in new artifacts:** bare `NOT_VERIFIED`, `NOT_VERIFIED_NO_ARTIFACT_MATCH`, and aliases in `claim_labels.DEPRECATED_CLAIM_ALIASES`.
- Do **not** invent a replacement for the retired MDD narrative. Use dated lineage MDDs (`VERIFIED_LINEAGE_MDD` / `PRIMARY_COMPARABLE_MDD`).
- Paper metrics stay labeled PAPER/RESEARCH — never restated as live achievement.

## 5. Dual-paper / observe ≠ cutover / stitch

- Observe OPEN and held-out PASS do **not** authorize Soft-Frozen flip, DEFAULT change, or live stitch.
- E45 live stitch stays **FORBIDDEN** until a dedicated second human stitch ACCEPT + checklist.
- Do not rewrite `forward/e21` history to “fix” recon.

## 6. First-class kwargs — no module monkeypatches

- Cost stress: `simulate_core(..., cost_multiple=)`.
- Sleeve-local overlays: `simulate_core(..., e45_sleeve_names=)` and `apply_exposure_to_sleeve_weights(..., sleeve_names=)`.
- **Forbidden in new paper scripts:** `setattr` on fee globals (`BUY_FEE`/`SELL_FEE`/`SLIP`/`TAX_*`); reassignment of `apply_exposure_to_sleeve_weights`.

## 7. Canonical book IDs

| Role | ID |
|---|---|
| Soft-Frozen early-stack base | `BASE_E16_E18_E22_v2s` |
| Full E45 E3 challenger | `CHAL_E45_E3` |
| Blend observe α=0.25 | `BLEND_E45_A25` |
| Other constant blends | `BLEND_E45_A{nn}` via `e45_paper_harness.book_id_for_alpha` |

- Do not invent `FULL_E45`, bare `BLEND_A05`, or `CHAL_E45_E3_FULL` in **new** emitters.
- Historical repro tables may keep old labels; regenerators should migrate to canonical IDs.

## 8. Shared harness — kill copy/paste

- New E45 paper screens import from `scripts/e45_paper_harness.py`:
  market load, blend exposure, window stats, claim status, book IDs, `run_early_stack`.
- Do not fork local `load_market` / `window_stats` / `blend` copies unless the harness cannot express the experiment.
- **Dual-alias ban (paper regenerators):** one script may use **at most one spelling** per book/window/harness family. Mixing canonical + fork in the same file fails `check_e45_paper_hygiene.py` (e.g. `heldout_2019_plus` with `held_out_2019_plus`, or `BASE_E16_E18_E22_v2s` with `BASE_E16_E18_E22`). Prefer harness constants / `WINDOWS_STANDARD` keys only.

## 9. Metric keys and paths

- NAV MDD key: **`max_drawdown`** (not `max_dd` / `maxdd` aliases in new code).
- Market: `forward/e21/live_market.csv`; dividends: `data/dividend_events/e22_dividend_events.csv`.
- Trust `research/` mirrors over `repro/` scratch when they disagree (`ARTIFACT_RETENTION.md`).

## 10. Repro hygiene

- Do not commit large fills / daily NAV dumps unless a charter requires it.
- Prefer `repro/<run>/reports/*.md|json` + small summary CSVs.
- Ignore `*_fills.csv` and bulky daily NAV under `repro/` (see `repro/.gitignore`).

## 11. Frozen / Soft-Frozen edit discipline

- Do not retune frozen E3 winner locks in place; scale via blend α or new **paper** profiles only.
- Soft-Frozen KEEP means operate the frozen core — challengers stay separate experiments.

## 12. Hygiene check

```bash
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
```

E45 checker: banned claim labels, fee/sleeve monkeypatches, non-canonical book IDs, **dual book/window aliases**.  
Project checker: also metric `or 0`/`or 9` on CAGR/MDD and Soft-Frozen clip list literals outside the single-source module.

Coverage map: `research/ops/CODING_STANDARDS_COVERAGE.md`.

## Label

`CODING_STANDARDS_2026-09-06__DUAL_ALIAS_BAN`
