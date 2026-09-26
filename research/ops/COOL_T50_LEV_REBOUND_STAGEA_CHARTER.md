# COOL 結束買台50正2（00631L）搶反彈 — Paper Charter (Stage A)

Date: 2026-09-26  
Status: **CHARTER OPEN · Stage A DONE → `MDD_BLOCK`** · Soft-Frozen live **KEEP** · live wire **false**  
Human mechanism (exact intent):

```
如果用00631L搶反彈呢 → 開這條 Stage A charter
```

Interpretation (binding):

| State | Action |
|---|---|
| **COOL defending** (`cool_exposure < 1`) | **OFF weight = 0**（不加槓桿） |
| **COOL exit day** (defending → full: prior `<1`, today `=1`) | Start **rebound pulse**: hold **台50正2 `00631L`** for **H** sessions |
| **After pulse / never exited** | **OFF = 0** |

Class: **A. Research / EXPERIMENTAL** · live tip / Soft-Frozen / universe expand = **Class D** later only  
Parent live: Soft-Frozen **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** + Soft+Sleeve + **`SELL_a75`** + `FUSE_ADDITIVE` + **`COOL_c8_f50_d21`**  
Capital **500M** · lot **1000** · Exact T+1 · E22 DEFAULT books  

Prior negative: COOL×`00632R` defend satellite / pulse → **CAGR hurt** (`COOL_INV_SOFT`). This charter tests the **opposite timing** (exit rebound), not inverse.

Label: `COOL_T50_LEV_REBOUND_STAGEA_CHARTER_2026-09-26__OPEN`

**Passing ≠ Soft-Frozen flip ≠ tip universe expand ≠ history rewrite.**

---

## Question

Vs `BASE_LIVE_FUSE_COOL` (live twin: Soft+Sleeve+FUSE+**SELL_a75**+COOL):

Does a predeclared **`00631L` pulse after COOL exit** lift held-out CAGR (≥ **+0.20 pp**) without blowing MDD / tip gates?

## Mechanism (finite)

1. Build live Soft-Frozen targets (live clips + Soft assist + Sleeve tilt + **sell amp 0.75**).  
2. Build frozen **`COOL_c8_f50_d21`** exposure from FUSE offense NAV.  
3. Scale equity sleeves by `cool_exposure` (same as live).  
4. Detect **exit entries**: first day of each streak where `cool` goes from `<1` → `1`.  
5. **OFF (`00631L`)** daily weight:

```
on exit day t0: pulse days t0 .. t0+H-1
OFF_t = α            if t in pulse and listed
OFF_t = 0            otherwise
equity_t *= (1 − OFF_t)   # funding from Soft sleeves (no invent cash)
```

6. Finite grid: `α ∈ {0.10, 0.25, 0.50}` · `H ∈ {3, 5, 10, 21}`.  
7. Pre-listing / missing `00631L` bars → force `OFF_t = 0` (no look-ahead invent).

**Controls**

- `BASE_LIVE_FUSE_COOL` — live twin（OFF=0）  
- `ALWAYS_A25` — α=0.25 every listed day（decay / abuse; not promote）  
- `DEFEND_A25_H5` — pulse on **defend entry** with α=0.25 H=5（wrong-timing control）

## Objective

Windows: **heldout_2019_plus** + **sealed_2023_plus** · tip YTD/1y.

| Gate | Rule |
|---|---|
| tip_clean | YTD + 1y tip window PASS |
| tip_mdd_ok | YTD & 1y MDD↑ ≥ **−0.5 pp** |
| held_mdd | held MDD↑ ≥ **−0.25 pp** |
| sealed_mdd | sealed MDD↑ ≥ **0** |
| cagr_floor | held CAGR↑ ≥ **+0.20 pp** |

```
score = 0.5×(CAGR↑_held + CAGR↑_sealed) + 0.5×(MDD↑_held + MDD↑_sealed)
```

| Verdict | Meaning |
|---|---|
| `COOL_LEV_REBOUND_HIT` | ≥1 book clears all gates |
| `COOL_LEV_REBOUND_SOFT` | MDD/tip OK but CAGR short of +0.20 |
| `MDD_BLOCK` | tip OK but MDD gate fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → **paper observe only**; live `00631L` membership = Class D ACCEPT.

## Out of scope / WON’T

- Retune COOL_c8 parameters  
- Soft-Frozen clip / tip rewrite  
- Stack DH+COOL · broker live-write  
- Permanent 正2 sleeve when defending  
- Reopen 00632R grids in this charter  
- 民股 / 4-sleeve reopen  

## Stage plan

| Stage | Action | Exit |
|---|---|---|
| **A** | Finite α×H grid · screen + decision pack | HIT / SOFT / MDD_BLOCK / NO_LIFT |
| **B** | Dual-paper observe on winners only | Separate ballot |
| **D** | Live universe + OFF wire | Human **ACCEPT** only |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_lev_rebound_stagea.py
```

Artifacts: `research/ops/COOL_T50_LEV_REBOUND_*` · `repro/cool-t50-lev-rebound-stagea/` · price `data/def_proxies/00631L_ohlcv.csv`

## Label

`COOL_T50_LEV_REBOUND_STAGEA_CHARTER_2026-09-26__OPEN`
