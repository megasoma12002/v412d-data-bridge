# FIN×SAT COMPOSITE Stage A — mix OPEN-observe strengths (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `COMPOSITE_HIT`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · live `CONF_RET3_A10_H5` **KEEP** · no live wire  
Parents (UP/DOWN 2026-09-28):
- FIN both-quality **`B_OR_K9_x_HARD150`** · OBSERVE OPEN · Stage B `BOTH_QUALITY_HIT`
- CONF densify **`SAT_A20_H5`** · OBSERVE OPEN · Stage A `MECH_HIT` · live α=0.10 KEEP

Human intent (normalized):

```
OPEN Stage A: COMPOSITE 取優混合 · FIN HARD150 × SAT_A20 · tip-safe + CAGR↑ · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_COMPOSITE_STAGEA_CHARTER_2026-09-28__DONE_COMPOSITE_HIT__NO_LIVE_WIRE`

## Why

Past research + observe UP/DOWN left two **OPEN** tip-clean-ish HIT ingredients on orthogonal actuators:
1. FIN within-sleeve buy×sell quality (`OR_K9` × hard sell NOT_BELOW_MA150)
2. COOL-exit satellite densify (`00631L` CONF α 0.10→0.20 H=5)

Belief: joint paper may clear held CAGR+MDD+tip where either alone is still observe-only.  
Risk: product hurts tip; or one parent already captures all lift (`PARENT_KEEP`).

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen clips · Exact T+1 · FUSE · COOL · SELL_a75 · KD_OPT · TEL T3 · FinPriv V7 | **KEEP** |
| Live CONF α=0.10 | **KEEP** until dedicated ACCEPT |
| Soft×Sleeve auto-fuse / Gate H combo | **FORBIDDEN** |
| 0050 tip-block / densify / regime NO_EDGE reopen | **OUT of mix** |
| CLOSED observes (soft/sleeve/BLEND/E45…) | **OUT** without new ballot |
| Live wire from Stage A | **forbidden** |

## Mechanism

Base twin: Soft-Frozen + FUSE Soft SELL_a75 + COOL_c8 + live KD buy_ok + CONF schedule α (satellite DEF=`00631L`).

| Actuator | Spec |
|---|---|
| FIN HARD150 | `buy_ok` AND (`BELOW_MA120`∨`K9_LT30`) · `fin_sell_ok` = NOT below MA150 |
| SAT densify | CONF RET3 · H=5 · α ∈ {0.10 live, 0.15, 0.20} |

## Gates (HIT)

1. held CAGR↑ ≥ **+0.15pp** (chal − base)  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & 1y MDD↑ ≥ **0**  
4. Diagnostic optional: FIN BUY or SELL WR↑ ≥ **+0.5pp** (soft if short → `WIN_SOFT`)

## Grid (finite ≤9)

| ID | FIN overlay | CONF α |
|---|---|---|
| `CTRL_LIVE_A10` | none | 0.10 (live) |
| `FIN_HARD150_A10` | OR_K9 × HARD150 | 0.10 |
| `SAT_A15_H5` | none | 0.15 |
| `SAT_A20_H5` | none | 0.20 |
| `COMP_H150_x_A15` | OR_K9 × HARD150 | 0.15 |
| `COMP_H150_x_A20` | OR_K9 × HARD150 | 0.20 |
| `COMP_H120_x_A20` | OR_K9 × HARD120 | 0.20 |
| `COMP_BUY_OR_K9_x_A20` | OR_K9 buy only | 0.20 |
| `COMP_SELL_H150_x_A20` | HARD150 sell only | 0.20 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `COMPOSITE_HIT` | ≥1 COMP_* clears all HIT gates |
| `WIN_SOFT` | economic clear; WR short |
| `PARENT_KEEP` | only FIN_* or SAT_* clears economic; joint fails |
| `CAGR_SOFT` / `TIP_BLOCK` / `NO_EDGE` | as usual |

Even HIT → **paper observe ballot only** (new composite observe — not auto cutover).

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_composite_stagea.py
```

Artifacts: `research/ops/FIN_SAT_COMPOSITE_STAGEA_*` · `repro/fin-sat-composite-stagea/`
