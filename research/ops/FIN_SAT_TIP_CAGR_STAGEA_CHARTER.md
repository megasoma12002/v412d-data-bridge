# FIN×SAT tip-CAGR Stage A — repair tip giveback (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · live `CONF_RET3_A10_H5` **KEEP** · COMPOSITE observe **KEEP OPEN** · no live wire  
Parent:
- FIN×SAT COMPOSITE **`COMP_H150_x_A20`** · OBSERVE OPEN · Stage A `COMPOSITE_HIT` · tip MDD↑ OK · tip CAGR giveback **PAUSE_REVIEW** (~13pp YTD)

Human intent (normalized):

```
OPEN Stage A: tip CAGR repair · keep tip MDD · Soft-Frozen KEEP · paper only · no live
```

Label: `FIN_SAT_TIP_CAGR_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

COMPOSITE observe wins held/sealed CAGR and tip **MDD**, but tip YTD/1y **CAGR giveback** (~13 / ~9 pp) blocks cutover.  
Diagnosis: tip drag skews to **FIN HARD150**; SAT densify alone was tip-CAGR positive.

Belief: a finite tip-first grid can find a book that is tip CAGR≥0 **and** tip MDD≥0 with non-trivial held lift — possibly milder densify, drop hard-sell, or SAT-led.  
Risk: tip-clean books lose held edge (`PARENT_KEEP` / `NO_EDGE`); or only SAT alone works (`SAT_KEEP`).

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · KD_OPT · TEL T3 · FinPriv V7 | **KEEP** |
| Live CONF α=0.10 | **KEEP** |
| COMPOSITE observe OPERATING | **KEEP** (do not CLOSE from this Stage A) |
| Soft×Sleeve Gate H | **FORBIDDEN** |
| Expand beyond finite grid after peek | **FORBIDDEN** |
| Live wire from Stage A | **forbidden** |

## Mechanism

Same twin as COMPOSITE: Soft-Frozen + SELL_a75 + COOL_c8 + KD buy_ok + CONF schedule (DEF=`00631L`).

| Actuator | Spec |
|---|---|
| FIN overlays | `OR_K9` buy · `HARD120`/`HARD150` sell · or buy-only |
| SAT densify | CONF RET3 · H=5 · α ∈ {0.10, 0.15, 0.20} |

## Gates (HIT) — tip CAGR binding

1. tip YTD **and** tip 1y **CAGR↑ ≥ 0** (chal − base) ← **new binding**  
2. tip YTD **and** tip 1y **MDD↑ ≥ 0**  
3. held CAGR↑ ≥ **+0.10pp**  
4. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**

HIT requires family `tip` (repair candidates), not ctrl/ref.

## Grid (finite ≤9)

| ID | fam | FIN | α |
|---|---|---|---:|
| `CTRL_LIVE_A10` | ctrl | none | 0.10 |
| `REF_COMP_H150_A20` | ref | OR_K9 × HARD150 | 0.20 |
| `REF_SAT_A20` | ref | none | 0.20 |
| `REF_FIN_H150_A10` | ref | OR_K9 × HARD150 | 0.10 |
| `TIP_H150_x_A15` | tip | OR_K9 × HARD150 | 0.15 |
| `TIP_H120_x_A15` | tip | OR_K9 × HARD120 | 0.15 |
| `TIP_BUY_OR_K9_x_A15` | tip | OR_K9 buy only | 0.15 |
| `TIP_BUY_OR_K9_x_A20` | tip | OR_K9 buy only | 0.20 |
| `TIP_SAT_A15` | tip | none | 0.15 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `TIP_CAGR_HIT` | ≥1 `tip` book clears all HIT gates |
| `SAT_KEEP` | only SAT-led tip-clean with held lift; FIN overlays fail tip CAGR |
| `TIP_MDD_ONLY` | tip MDD OK but tip CAGR fail (COMPOSITE-like) |
| `HELD_SOFT` / `TIP_BLOCK` / `NO_EDGE` | as labeled |

Even HIT → **paper observe ballot DRAFT only** (not auto replace COMPOSITE observe / not live).

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tip_cagr_stagea.py
```

Artifacts: `research/ops/FIN_SAT_TIP_CAGR_STAGEA_*` · `repro/fin-sat-tip-cagr-stagea/`  
Register: **0k9c**
