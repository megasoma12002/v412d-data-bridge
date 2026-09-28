# FIN×SAT tip new-mech Stage A — COOL-conditional HARD + SAT-relax (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · live `CONF_RET3_A10_H5` **KEEP** · COMPOSITE observe **KEEP OPEN** · no live wire  
Parents:
- tip-CAGR Stage A **`TIP_MDD_ONLY`** (0k9c) — HARD overlays tip CAGR−; SAT tip-clean but held short
- ABC-A HARD150 tip-repair **`LOCK_KEEP_NO_TIP_LIFT`** — season/MA/dampen grid exhausted (no SAT)

Human intent (normalized):

```
OPEN Stage A: tip new-mech · COOL-conditional HARD sell · OR SAT-only relaxed held ballot · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_TIP_MECH_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

0k9c showed tip CAGR drag is **FIN HARD**, not densify; SAT-only is tip-clean but fails strict held.  
Season/MA retune already failed (ABC-A). This round tests **new actuators**:

1. **COOL-conditional HARD150** — apply hard-sell only in COOL-defend **or** only risk-on (COOLOFF)  
2. **SAT-only relaxed held** — dedicated ballot gates: tip-clean + held CAGR≥+0.05 · held MDD≥−0.40

Belief: COOL gating may cut tip-window hard-sell damage; or SAT_RELAX is an honest tip-first observe path.  
Risk: both miss → `NO_EDGE` / `TIP_MDD_ONLY`; do not reopen exhausted HARD×α / season grids.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE observe OPERATING | **KEEP** |
| Re-run HARD×α densify / season tip-repair grids | **FORBIDDEN** |
| Soft×Sleeve Gate H | **FORBIDDEN** |
| Live wire from Stage A | **forbidden** |

## Mechanism

| Track | Spec |
|---|---|
| `HARD150_COOLON` | `fin_sell_ok` = HARD150 **only when** COOL exposure &lt; 1; else unrestricted |
| `HARD150_COOLOFF` | HARD150 **only when** COOL exposure ≥ 1; else unrestricted |
| Buy | live KD + optional `OR_K9` |
| SAT | CONF RET3 H=5 · α ∈ {0.10, 0.15, 0.20} |
| SAT_RELAX | no FIN overlay · densify only · **relaxed held gates** |

## Gates

### MECH HIT (`mech` family — strict)

1. tip YTD & 1y CAGR↑ ≥ **0**  
2. tip YTD & 1y MDD↑ ≥ **0**  
3. held CAGR↑ ≥ **+0.10pp**  
4. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**

### SAT_RELAX HIT (`sat` family — ballot)

1. tip YTD & 1y CAGR↑ ≥ **0** · tip MDD↑ ≥ **0**  
2. held CAGR↑ ≥ **+0.05pp**  
3. held MDD↑ ≥ **−0.40pp** · \|MDD\| ≤ **15%**

## Grid (finite ≤9)

| ID | fam | FIN sell | buy | α |
|---|---|---|---|---:|
| `CTRL_LIVE_A10` | ctrl | none | none | 0.10 |
| `REF_COMP_H150_A20` | ref | HARD150 always | OR_K9 | 0.20 |
| `MECH_H150_COOLON_A10` | mech | HARD150 COOLON | OR_K9 | 0.10 |
| `MECH_H150_COOLOFF_A10` | mech | HARD150 COOLOFF | OR_K9 | 0.10 |
| `MECH_H150_COOLON_A15` | mech | HARD150 COOLON | OR_K9 | 0.15 |
| `MECH_H150_COOLOFF_A15` | mech | HARD150 COOLOFF | OR_K9 | 0.15 |
| `MECH_H150_COOLON_A20` | mech | HARD150 COOLON | OR_K9 | 0.20 |
| `SAT_A15_RELAX` | sat | none | none | 0.15 |
| `SAT_A20_RELAX` | sat | none | none | 0.20 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `MECH_HIT` | ≥1 `mech` clears strict tip+held |
| `SAT_RELAX_HIT` | ≥1 `sat` clears relaxed tip+held (no mech HIT) |
| `TIP_MDD_ONLY` | economic/tip-MDD without tip CAGR |
| `TIP_BLOCK` / `NO_EDGE` | as labeled |

Even HIT → **paper observe ballot DRAFT only** · COMPOSITE observe not auto-CLOSED · no live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tip_mech_stagea.py
```

Register: **0k9d**
