# Soft-Frozen Clip Search Charter — Research Only

Date: 2026-09-07  
Status: **CHARTER DRAFT / OPEN** — awaiting human **ACCEPT charter** (research only)  
Class: **A. Research / EXPERIMENTAL** (`STRATEGY_UPDATE_STANDARD_PROCESS.md`)  
Soft-Frozen live: **KEEP** — FIN **[0.50, 0.95]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]**  
Execution context (fixed for this charter): board-lot **1000** · capital **15M** · books **`E22_v2s_tw`**

Authority: `STRATEGY_UPDATE_STANDARD_PROCESS.md` · `E50_RESEARCH_OPERATING_RULES.md` · `HUMAN_DECISION_REGISTER.md` · `SOFT_FROZEN_TEL_ETF_FLOOR_10_WITHDRAWN_2026-09-07.md`

**Passing this charter ≠ Soft-Frozen flip ≠ live cutover.**

---

## Problem

Sleeve clip bounds (FIN / TEL / 0050 `[lo, hi]`) strongly affect:

- mean sleeve weights and cash residual under **整張 1000**
- full / held-out / sealed **MDD vs CAGR** tradeoff
- whether TEL / 0050 can fill ≥1 張 at current capital

Live Soft-Frozen must stay human-gated. Blind “AI 調完美比例” is forbidden as a live path.  
This charter defines a **research-only** search for **challenger clip boxes**, with predeclared objectives and anti-leakage splits.

Withdrawn note: TEL/0050 floor-10 ACCEPT was **closed without merge** (#119). Any future floor change still needs a **separate Class D** Soft-Frozen PR — not this charter’s Stage B/C alone.

---

## In scope

1. Predeclare a **finite clip search space** and **objective** (no sealed peeking for selection).  
2. Implement a **paper-only** clip challenger harness (grid and/or Bayesian; optional ML surrogate later).  
3. Report OOF → validation → **sealed** metrics for **pre-registered** candidates only.  
4. Emit dual-paper / observe artifacts under a **new challenger id** (not Soft-Frozen).  
5. Decision pack path: human may later ACCEPT a **Class D** Soft-Frozen flip citing this evidence — never auto-flip.

## Out of scope / WON’T

- Edit `scripts/e16_soft_frozen_base.py` live constants in this charter’s implementation PRs  
- Rewrite `forward/e21` history  
- E45 stitch / overlay live-wire  
- Use sealed window to **choose** clips (sealed = **report only** after lock)  
- Claim “optimal / perfect” ratios  
- Retune the same challenger id after held-out fail (new id required)  
- Bundle Soft-Frozen flip with searcher code in one PR  

---

## Search space (predeclared)

Coordinate order: `(FIN_lo, FIN_hi, TEL_lo, TEL_hi, ETF_lo, ETF_hi)` with simplex-feasible floors:

`FIN_lo + TEL_lo + ETF_lo ≤ 1` and each `lo ≤ hi` within sleeve caps below.

| Sleeve | Live Soft-Frozen (KEEP) | Research search box (inclusive) | Step (grid) |
|---|---|---|---|
| Financial | [0.50, 0.95] | lo ∈ {0.45, 0.50, 0.55, 0.60} · hi ∈ {0.85, 0.90, 0.95} | as listed |
| Telecom | [0.03, 0.35] | lo ∈ {0.03, 0.05, 0.08, 0.10, 0.12} · hi ∈ {0.25, 0.30, 0.35} | as listed |
| 0050 | [0.00, 0.35] | lo ∈ {0.00, 0.05, 0.08, 0.10} · hi ∈ {0.25, 0.30, 0.35} | as listed |

Hard filters (drop before sim):

- `hi − lo ≥ 0.05` per sleeve  
- `FIN_lo + TEL_lo + ETF_lo ≤ 0.95`  
- Exclude the **exact live Soft-Frozen tuple** from “winner” labeling (it remains **BASE** control)

**Bayesian / surrogate (optional Stage C):** same bounds; acquisition may use OOF+validation only; sealed locked until Stage D report.

**ML note:** gradient / RL weight learners are **out of Stage B**. If proposed later, need a **new charter amendment** (new leakage surface).

---

## Objective (predeclared — do not retune after seeing sealed)

Primary score on **held-out 2019+** (vs Soft-Frozen BASE @ same capital/lot/books):

```
score = MDD_improve_pp − 0.5 × |CAGR_giveback_pp|
```

where `MDD_improve_pp = 100 × (MDD_base − MDD_chal)` in signed drawdown units  
(more positive = shallower challenger drawdown).

Secondary (report only; not for selection):

- sealed 2023+ MDD / CAGR  
- validation 2019–2022 stability  
- tip cash residual / TEL+0050 fill rate under board-lot 1000  
- turnover proxy (`n_fills`)

Stop / fail:

| Result | Action |
|---|---|
| No candidate score > 0 on held-out | **STOP** search family; do not Soft-Frozen-talk |
| Top candidate sealed MDD worse by >2pp vs BASE | Label **FRAGILE**; observe only; no Class D ballot |
| Held-out used for tuning then re-used as pass | **Invalid** — new challenger id + new held-out rule |

---

## Windows (fixed)

| Window | Dates | Role |
|---|---|---|
| OOF | 2011–2018 | Screen / Bayesian fit only |
| Validation | 2019–2022 | Rank / early stop |
| Held-out | 2019+ | **Primary selection** |
| Sealed | 2023+ | **Frozen report** after candidate lock |
| Full | all | Diagnostics only |

Execution: Exact T+1 · `E22_v2s_tw` · `lot_size=1000` · `capital=15_000_000`.

---

## Pass / fail

| Gate | Pass |
|---|---|
| Soft-Frozen | Live module **bit-identical**; searcher reads copy / override kwargs only |
| Identity | Challenger id `CLIP_SEARCH_<rule>` never overwrites BASE id |
| Exact T+1 | `exact_t1_ok` |
| Board-lot | fills multiples of 1000 |
| Split honesty | Sealed not used for selection |
| Artifacts | `repro/clip-search-<stamp>/` + research MD/JSON |
| Live | **No** `forward/e21` edit from this charter |

Fail → stay research; Soft-Frozen KEEP.

---

## Stage plan

```
A  ACCEPT charter (this file + decision pack)     ← YOU ARE HERE
B  Grid harness + BASE control @ 15M/1000         paper only
C  Optional Bayesian within same box              paper only
D  Lock ≤3 candidates; sealed report              paper only
E  Dual-paper / month-end observe (if score>0)    observe only
F  Class D Soft-Frozen ballot (separate)          human only; optional
```

## Naming

| Artifact | Path |
|---|---|
| Charter | `research/ops/SOFT_FROZEN_CLIP_SEARCH_CHARTER.md` |
| Decision pack | `research/ops/SOFT_FROZEN_CLIP_SEARCH_DECISION_PACK.md` |
| Repro | `repro/clip-search-<YYYYMMDD>/` |
| Challenger module (future) | `scripts/e16_clip_search_challenger.py` (must not edit Soft-Frozen singlesource) |

---

## Human ballot (charter level)

See **`SOFT_FROZEN_CLIP_SEARCH_DECISION_PACK.md`**.

| Ballot | Effect |
|---|---|
| **ACCEPT charter** | Stage B implementation PRs allowed (paper only) |
| **REJECT / DEFER** | No searcher; Soft-Frozen KEEP |

Soft-Frozen flip remains a **different** ballot (Class D), even if search finds a strong box.
