# COOL × 00631L 短線輔助 — Paper Charter (Stage A, tracks 1–4)

Date: 2026-09-26  
Status: **CHARTER OPEN · Stage A DONE → `SHORT_ASSIST_HIT`** · Soft-Frozen live **KEEP** · live wire **false**  
Parent: `COOL_T50_LEV_REBOUND_*` verdict **`MDD_BLOCK`** (α≥0.10 × H≥3 exit pulse)  
Human: **除第五條（near-flat 改門檻）其它都研究** — 短線輔助 `00631L`

Class: **A. Research / EXPERIMENTAL** · no Soft-Frozen flip · no tip rewrite · no live wire from Stage A  

Live twin baseline: Soft-Frozen clips + Soft+Sleeve + **`SELL_a75`** + `FUSE_ADDITIVE` + **`COOL_c8_f50_d21`**

Label: `COOL_T50_LEV_SHORT_ASSIST_STAGEA_CHARTER_2026-09-26__OPEN`

**Passing ≠ live · ≠ Class D membership · ≠ near-flat policy change (track 5 OUT OF SCOPE).**

---

## Question

Can any **short-assist** `00631L` mechanism (thinner / confirmed / stop / residual-budget) clear held CAGR≥**+0.20pp** and MDD/tip gates vs `BASE_LIVE_FUSE_COOL`?

## Tracks (finite)

### T1 — THIN short pulse
Exit pulse as parent, but thinner/shorter:  
`α ∈ {0.03, 0.05, 0.08}` · `H ∈ {1, 2}`

### T2 — CONFIRM entry
Exit pulse only if **confirmation** on exit day `t0`:

| id | Confirm |
|---|---|
| `RET1` | 0050 close ret₁ > 0 |
| `RET3` | 0050 close ret₃ > 0 |
| `RET1_PX` | RET1 and `proxy_mdd63 > −EXIT_X` (0.06) |

Grid: confirm × `α ∈ {0.10, 0.25}` × `H ∈ {3, 5}`

### T3 — STOP inside pulse
Exit pulse with **satellite stop**: from entry, if `00631L` close/entry −1 ≤ `−stop`, clear OFF for rest of pulse.  
`α ∈ {0.10, 0.25}` · `H ∈ {5, 10}` · `stop ∈ {0.03, 0.05}`

### T4 — RESIDUAL budget
On COOL exit, size OFF from **released residual** only:  
`OFF_t = α × (1 − cool_{t0−1})` for `H` sessions (capped ≤ α).  
`α ∈ {0.50, 1.00}` · `H ∈ {1, 2, 3}`

### Controls
- `BASE_LIVE_FUSE_COOL`  
- `PARENT_A10_H5` — parent best tip-OK-ish cell (reference; not re-promote)

## Gates / verdicts

Same as parent rebound charter:

| Gate | Rule |
|---|---|
| tip_clean / tip_mdd_ok | YTD+1y PASS · MDD↑ ≥ −0.5pp |
| held_mdd / sealed_mdd | ≥ −0.25pp / ≥ 0 |
| cagr_floor | held CAGR↑ ≥ +0.20pp |

| Verdict | Meaning |
|---|---|
| `SHORT_ASSIST_HIT` | ≥1 book clears all |
| `SHORT_ASSIST_SOFT` | MDD/tip OK · CAGR short |
| `MDD_BLOCK` | tip OK · MDD fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → paper observe only.

## Out of scope

- Track 5 near-flat / floor change  
- Retune COOL params · Soft-Frozen flip · tip rewrite · broker  
- Permanent 正2 · defend-window 正2 reopen  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_lev_short_assist_stagea.py
```

Artifacts: `research/ops/COOL_T50_LEV_SHORT_ASSIST_*` · `repro/cool-t50-lev-short-assist-stagea/` · `data/def_proxies/00631L_ohlcv.csv`

## Label

`COOL_T50_LEV_SHORT_ASSIST_STAGEA_CHARTER_2026-09-26__OPEN`
