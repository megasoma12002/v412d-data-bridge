# COOL 啟動買台50反1／結束賣出 — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **CHARTER OPEN · Stage A DONE → `COOL_INV_SOFT`** · Soft-Frozen live **KEEP** · live wire **false**  
Human mechanism (exact):

```
Cool機制成立時買t50反一 cool結束時賣出
```

Interpretation (binding):

| State | Action |
|---|---|
| **COOL defending** (`cool_exposure = FLOOR=0.50`) | Hold **台50反1 `00632R`** as DEF satellite |
| **COOL not defending** (`cool_exposure = 1.0`, incl. post-exit cool-down days) | **DEF weight = 0**（賣出／不加碼） |

Class: **A. Research / EXPERIMENTAL** · live tip / Soft-Frozen flip = **Class D** later only  
Parent live: Soft-Frozen **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** + Soft+Sleeve + `FUSE_ADDITIVE` + **`COOL_c8_f50_d21`**  
Capital **500M** · lot **1000** · Exact T+1 · E22 DEFAULT books  

Label: `COOL_T50_INV_SATELLITE_CHARTER_2026-09-25__STAGE_A_OPEN`

**Passing ≠ Soft-Frozen flip ≠ tip universe expand ≠ history rewrite.**

---

## Question

Vs `BASE_LIVE_FUSE_COOL` (live twin: Soft+Sleeve+FUSE+COOL, cash residual while defending):

Does parking a predeclared fraction of the **COOL residual** into **`00632R`** only while defending lift held-out CAGR (≥ **+0.20 pp**) without blowing MDD / tip gates?

## Mechanism (finite)

1. Build live Soft-Frozen targets (live clips + Soft assist + Sleeve tilt).  
2. Build frozen **`COOL_c8_f50_d21`** exposure from FUSE offense NAV (same as live paper twin).  
3. Scale equity sleeves (Financial / Telecom / 0050) by `cool_exposure`.  
4. **DEF (`00632R`)** daily weight:

```
residual_t = 1 - cool_exposure_t
DEF_t = α × residual_t    if cool_exposure_t < 1 − ε
DEF_t = 0                 otherwise   # cool 結束 → 賣出
```

5. `α ∈ {0.25, 0.50, 1.00}` — fraction of residual into 反1（其餘仍現金）.  
6. Pre-listing / missing `00632R` bars → force `DEF_t = 0` (no look-ahead invent).

**Controls**

- `BASE_LIVE_FUSE_COOL` — live twin（DEF=0；殘差現金）  
- `ALWAYS_A50` — α=0.50 but DEF on **every** day with residual-like 0.25 weight even when not defending（sanity / abuse check; not a promote candidate）

## Objective

Windows: **heldout_2019_plus** + **sealed_2023_plus** · tip YTD/1y.

| Gate | Rule |
|---|---|
| tip_clean | YTD + 1y CAGR tip PASS |
| tip_mdd_ok | YTD & 1y MDD↑ ≥ **−0.5 pp** |
| held_mdd | held MDD↑ ≥ **−0.25 pp**（近持平） |
| sealed_mdd | sealed MDD↑ ≥ **0** |
| cagr_floor | held CAGR↑ ≥ **+0.20 pp** |

```
score = 0.5×(CAGR↑_held + CAGR↑_sealed) + 0.5×(MDD↑_held + MDD↑_sealed)
```

| Verdict | Meaning |
|---|---|
| `COOL_INV_HIT` | ≥1 book clears all gates |
| `COOL_INV_SOFT` | MDD/tip OK but CAGR short of +0.20 |
| `MDD_BLOCK` | tip OK but MDD gate fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → **paper observe only**; live `00632R` membership = Class D ACCEPT.

## Out of scope / WON’T

- Retune COOL_c8 parameters (x/floor/exit/dwell/cool)  
- Soft-Frozen clip / tip rewrite  
- Stack DH+COOL · broker live-write  
- Permanent 反1 sleeve when not defending（except sanity control）  
- 民股 / 4-sleeve reopen in this charter  

## Stage plan

| Stage | Action | Exit |
|---|---|---|
| **A** | Finite α grid · screen + decision pack | HIT / SOFT / MDD_BLOCK / NO_LIFT |
| **B** | Dual-paper observe on winners only | Separate ballot |
| **D** | Live universe + DEF wire | Human **ACCEPT** only |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_inv_satellite_stagea.py
```

Artifacts: `research/ops/COOL_T50_INV_SATELLITE_*` · `repro/cool-t50-inv-satellite-stagea/` · price `data/def_proxies/00632R_ohlcv.csv`

## Label

`COOL_T50_INV_SATELLITE_CHARTER_2026-09-25__STAGE_A_OPEN`
