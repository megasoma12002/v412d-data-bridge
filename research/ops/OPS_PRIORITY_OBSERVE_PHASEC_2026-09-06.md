# Ops Priority Follow-up — Observe PAUSE Refresh + Phase C `0050` Root-Cause

Generated: 2026-09-06  
Status: **OPS / PAPER DIAG** — Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · stitch **FORBIDDEN**  
Claimed −13.16%: **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

Label: `OPS_PRIORITY_OBSERVE_PHASEC_2026-09-06__STITCH_FORBIDDEN`

## Why this batch

After naming Medium cleanup (#90) merged, next priority was **not** another E45 α grid. It was:

1. Refresh observe trailing PAUSE tip (ops truth)
2. Root-cause sealed Phase C C1 DRIFT on `0050`

## 1) Observe PAUSE refresh

Artifact: `research/ops/E45_OBSERVE_PAUSE_REFRESH.md`  
Runner: `scripts/e45_observe_pause_refresh.py`

| Sleeve | Tip asof | YTD | 1y |
|---|---|---|---|
| `CHAL_E45_E3` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW |
| `BLEND_E45_A25` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW |
| `BLEND_E45_A05` | 2026-09-04 | ALERT | PAUSE_REVIEW |
| `SLEEVE_FIN_ONLY_A10` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW |

**Read:** tip still PAUSE/ALERT-dominated. Historical first-clean dates (where present) have relapsed. **No stitch discussion.**

## 2) Phase C `0050` sealed C1 DRIFT root-cause

Artifact: `research/ops/DATA_SOURCE_PHASE_C_0050_ROOTCAUSE.md`  
Runner: `scripts/data_source_phase_c_0050_rootcause.py`

| Metric | Value |
|---|---|
| Root class | **`UNADJUSTED_CLOSE_SPIKE`** |
| Sealed corr (all) | ~0.50 (DRIFT) |
| Sealed corr drop \|Δret\|>5pp | **~0.998** (recovers) |
| Outlier days | 2014-01-02 (Yahoo-side), **2025-06-18 (live raw close)** |
| Live evidence 2025-06 | raw close ~188→~47 while `adj_close` continuous (split/unit break) |
| C2 adj sealed | already **PASS** (prior follow-up) |

**Read:** not broad vendor rot. Do **not** flip Soft-Frozen / DEFAULT / e21 primary on this alone. Prefer adj/C2 path for `0050` QC; quarantine the two spike days if regenerating C1.

## Non-actions

- No Soft-Frozen / DEFAULT ballot
- No live stitch / no HIGH_BETA OPEN
- No −13.16% reinvention
- No Goodinfo/Wantgoo/CMoney reopen
- No silent e21 primary switch

## Suggested next (still ops, not α-search)

1. Keep month-end observe cadence; only revisit stitch if tip clears **and** second human ACCEPT exists
2. Optional: C1 builder patch to use adj_close for ETF `0050` or spike quarantine
3. Human ballots only if intentionally changing Soft-Frozen / DEFAULT / HIGH_BETA
