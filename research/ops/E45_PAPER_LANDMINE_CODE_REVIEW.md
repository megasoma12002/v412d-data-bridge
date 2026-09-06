# E45 Paper Landmine Code Review

Date: 2026-09-06  
Scope: E45 paper research track (roadmap #1–#7) + prior project code-review themes (#55/#56)  
Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · live stitch **FORBIDDEN**  
Coding rules extracted here → `research/ops/CODING_STANDARDS.md`

## Verdict

Paper research hit recurring engineering landmines (claim-label drift, book-ID forks, fee/sleeve monkeypatches, copy/paste harnesses, repro bloat). High-value hardening is in place; remaining items are hygiene / regenerator migrations, not Soft-Frozen or stitch work.

## Past code-review themes (still binding)

| Theme | Source | Rule |
|---|---|---|
| Soft-Frozen single-source | #55 | Clip only from `e16_soft_frozen_base.py` |
| Exact T+1 fail-closed | #55/#56 | Same-bar fills hard-fail; QC preserves `exact_t1_ok` |
| `None` ≠ `0` | #55/#56 | `mdd_delta_pp` / `cagr_delta_pp`; no `or 0`/`or 9` on MDD |
| Dual-paper ≠ cutover | debt board / claim policy | Observe PASS ≠ Soft-Frozen flip |
| Claim honesty | path A retirement | −13.16% = `RETIRED_HISTORICAL_NARRATIVE`; no invented replacement |
| No history rewrite | ops | Never rewrite `forward/e21` to “fix” recon |

## Landmines found this research

### P0 — correctness / governance

| # | Landmine | Impact | Fix |
|---|---|---|---|
| L1 | Claim-status drift: generators still emitted bare `NOT_VERIFIED` after path A retired the narrative | Stale ops packs / verify scripts contradict `CLAIMED_MDD_STATUS` | Emit `e45_crisis_core.CLAIMED_MDD_STATUS`; stage3 / v4v5 / verify_mdd updated |
| L2 | Book-ID collision: `FULL_E45` / `BLEND_A05` / dashboard aliases vs observe `CHAL_E45_E3` / `BLEND_E45_A25` | Cross-run joins break; humans misread observe sleeves | Canonical IDs in `e45_paper_harness`; dashboard labels aligned; regenerators migrate |
| L3 | Fee monkeypatch (`setattr` on `BUY_FEE`/…) | Parallel runs / forgotten restore corrupt later sims | `simulate_core(..., cost_multiple=)` first-class |
| L4 | Sleeve monkeypatch (rebind `apply_exposure_to_sleeve_weights`) | Same fragility for sleeve-local screens | `sleeve_names=` + `e45_sleeve_names=` first-class |
| L5 | Repro bloat (`*_fills.csv`, large daily NAV tracked) | Repo noise; accidental huge commits | Strengthen `repro/.gitignore`; prefer reports + summaries |

### P1 — maintainability

| # | Landmine | Fix |
|---|---|---|
| L6 | Copy/paste `load_market` / `window_stats` / `blend` across ≥10 paper scripts | `scripts/e45_paper_harness.py` |
| L7 | Path / fee / MDD key aliases (`mdd` vs `max_drawdown`) | Standards + helpers; new code uses `max_drawdown` |
| L8 | Historical MD still saying `NOT_VERIFIED` | Leave dated snapshots; regenerators emit retired status |

## Hardening shipped this pass

1. `apply_exposure_to_sleeve_weights(..., sleeve_names=)`
2. `simulate_core(..., cost_multiple=, e45_sleeve_names=)` + meta fields
3. `scripts/e45_paper_harness.py` — canonical books, claim, market, blend, windows, `run_early_stack`
4. Cost / sleeve-local / v4v5 scripts off monkeypatches
5. Claim emitters (stage3, v4v5, verify_mdd) → `CLAIMED_MDD_STATUS`
6. Dual-sleeve dashboard observe labels → `CHAL_E45_E3` / `BLEND_E45_A25`
7. `scripts/check_e45_paper_hygiene.py`
8. `research/ops/CODING_STANDARDS.md` + this review

## Explicit non-goals

- Live stitch / Soft-Frozen / DEFAULT flip
- Auto-open α=0.05 or sleeve-local observe
- Invent −13.16% replacement number
- Retune frozen E3 winner lock in place

## Cross-cut research note (unchanged)

Best simple intensity remains **constant blend α=0.05** (paper); observe sleeves stay **FULL/`CHAL_E45_E3` + `BLEND_E45_A25`**; stitch still forbidden.

## Label

`E45_PAPER_LANDMINE_CODE_REVIEW_2026-09-06`
