# COOL dual-handoff — 防守反1 → 結束正2 — Paper Charter (Stage A)

Date: 2026-09-26  
Status: **CHARTER OPEN · Stage A RUNNING** · Soft-Frozen live **KEEP** · live wire **false**  
Human: **開 dual-handoff Stage A**

Parents (binding priors — do not rewrite):

| Leg | Verdict | Pack |
|---|---|---|
| COOL defending → `00632R` | **`COOL_INV_SOFT`** | `COOL_T50_INV_SATELLITE_DECISION_PACK.md` |
| COOL exit → `00631L` CONFIRM | **`SHORT_ASSIST_HIT`** (observe OPEN) | `COOL_T50_LEV_SHORT_ASSIST_DECISION_PACK.md` |
| Plain exit rebound `00631L` | **`MDD_BLOCK`** | `COOL_T50_LEV_REBOUND_DECISION_PACK.md` |

Class: **A. Research / EXPERIMENTAL** · no Soft-Frozen flip · no tip rewrite · no live wire from Stage A  

Live twin baseline: Soft-Frozen clips + Soft+Sleeve + **`SELL_a75`** + `FUSE_ADDITIVE` + **`COOL_c8_f50_d21`**

Label: `COOL_T50_DUAL_HANDOFF_STAGEA_CHARTER_2026-09-26__OPEN`

**Passing ≠ live · ≠ Class D membership for `00632R` / `00631L` · ≠ compose from separate-leg HIT.**

---

## Question

Vs `BASE_LIVE_FUSE_COOL`: does **stacking** defend-window `00632R` **then** exit-pulse `00631L` (mutual-exclusion handoff) clear held CAGR≥**+0.20pp** and MDD/tip gates?

Separate-leg results do **not** imply the stack clears — INV alone hurts CAGR; LEV HIT sits on cash residual, not INV.

## Mechanism (finite)

1. Live Soft+Sleeve+FUSE+COOL twin (SELL_a75).  
2. **DEF = `00632R`** while COOL defending: `DEF_t = α_inv × (1 − cool_t)` (same as INV satellite).  
3. **OFF = `00631L`** on COOL exit pulse (optional CONFIRM), sticky **H** sessions: `OFF_t = α_lev`.  
4. **Handoff lock:** while `OFF_t > 0`, force `DEF_t = 0` (no simultaneous long+short levered).  
5. Soft equity sleeves scale by `cool_t × (1 − OFF_t)`.  
6. Pre-list / missing bars → that satellite weight 0.

### Challenger grid (finite)

| id pattern | α_inv | confirm | α_lev | H |
|---|---:|---|---:|---:|
| `DH_I25_L_RET3_A10_H5` | 0.25 | RET3 | 0.10 | 5 |
| `DH_I25_L_RET3_A10_H3` | 0.25 | RET3 | 0.10 | 3 |
| `DH_I25_L_RET1_A10_H3` | 0.25 | RET1 | 0.10 | 3 |
| `DH_I10_L_RET3_A10_H5` | 0.10 | RET3 | 0.10 | 5 |
| `DH_I25_L_RET3_A05_H5` | 0.25 | RET3 | 0.05 | 5 |
| `DH_I25_L_NONE_A10_H5` | 0.25 | NONE | 0.10 | 5 |

### Controls (reference — not promote)

- `BASE_LIVE_FUSE_COOL`  
- `REF_INV_A25` — INV-only α=0.25 (prior SOFT)  
- `REF_LEV_RET3_A10_H5` — LEV-only CONFIRM RET3 (prior HIT / observe champion)

## Gates / verdicts

Same floors as INV / short-assist parents:

| Gate | Rule |
|---|---|
| tip_clean / tip_mdd_ok | YTD+1y PASS · MDD↑ ≥ −0.5pp |
| held_mdd / sealed_mdd | ≥ −0.25pp / ≥ 0 |
| cagr_floor | held CAGR↑ ≥ +0.20pp |

| Verdict | Meaning |
|---|---|
| `DUAL_HANDOFF_HIT` | ≥1 dual book clears all |
| `DUAL_HANDOFF_SOFT` | MDD/tip OK · CAGR short |
| `MDD_BLOCK` | tip OK · MDD fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → paper observe only; dual Class D ACCEPT required for live.

## Out of scope

- Retune COOL params · Soft-Frozen flip · tip rewrite · broker  
- Simultaneous INV+LEV (forbidden by handoff lock)  
- Near-flat floor change · permanent 反1/正2 sleeves  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_dual_handoff_stagea.py
```

Artifacts: `research/ops/COOL_T50_DUAL_HANDOFF_*` · `repro/cool-t50-dual-handoff-stagea/` · `data/def_proxies/00632R_ohlcv.csv` · `data/def_proxies/00631L_ohlcv.csv`

## Label

`COOL_T50_DUAL_HANDOFF_STAGEA_CHARTER_2026-09-26__OPEN`
