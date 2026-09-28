# FIN buy-quality Stage C — A∪B hybrid (paper)

Date: 2026-09-28  
Status: **Stage C DONE — `HYBRID_PARETO`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · no live wire  
Parents: Stage A seed `SEED_MA120` (CAGR↑) · Stage B HIT `B_MA120_OR_K9` (WR↑ + MDD↑)  
Human intent:

```
OPEN Stage C: FIN buy-quality · keep Stage A CAGR edge + Stage B WR/MDD · hybrid paper only
```

Label: `FIN_BUY_QUALITY_STAGEC_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why Stage C

| Parent | Strength | Weakness |
|---|---|---|
| `SEED_MA120` (A) | held CAGR↑ ~+1.63pp | buy WR slightly down |
| `B_MA120_OR_K9` (B) | buy WR↑ ~+1.2pp · MDD↑ ~+2pp | CAGR only ~+0.67pp |

Stage C asks whether a **finite hybrid** can keep more of A's CAGR while retaining B's WR/MDD (Pareto vs both parents), without live wire.

## Question

On `BASE_LIVE_FUSE_COOL`, does ≥1 hybrid:

1. clear Stage B HIT gates (CAGR≥+0.15 · MDD near-flat · tip≥0 · WR↑≥+1.0pp), **and**
2. improve vs seed on WR (≥ seed WR +0.5pp) **and** vs B-HIT on CAGR (≥ B CAGR +0.15pp)?

If (2) fails but (1) holds → still `BUY_QUALITY_HIT` (may equal B).  
If only observe-eligible vs parents → `PARENT_KEEP_B` / `HYBRID_SOFT`.

## Non-actions

- Soft-Frozen / Exact T+1 / tip rewrite · live wire · broker  
- Re-open sell loss-defer · unbounded new filter families  

## Grid (finite)

| ID | Spec |
|---|---|
| `CTRL_BASE` | Control |
| `P_SEED_MA120` | Parent A — hard `BELOW_MA120` |
| `P_B_OR_K9` | Parent B — `MA120 ∨ K9_LT30` |
| `C_OR_K9_KD_ONLY` | Soft OR only **in** KD season; else hard MA120 |
| `C_OR_K9_OFF_ONLY` | Soft OR only **outside** KD season; else hard MA120 |
| `C_OR_K9_COOL1` | Soft OR only when cool=1; else hard MA120 |
| `C_OR_K9_AND_RSI50` | `MA120 ∨ (K9 ∧ RSI14&lt;50)` |
| `C_OR_K9_AND_BELOW_MA60` | `MA120 ∨ (K9 ∧ BELOW_MA60)` |
| `C_MA150_OR_K9` | looser MA150 ∨ K9 |
| `C_MA100_OR_K9` | tighter MA100 ∨ K9 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `HYBRID_PARETO` | HIT + beats seed on WR + beats B on CAGR |
| `BUY_QUALITY_HIT` | HIT gates clear (may be B-equivalent) |
| `HYBRID_SOFT` | observe-ok hybrid; no HIT |
| `PARENT_KEEP_B` | no hybrid beats B; keep B observe |
| `MDD_BLOCK` / `NO_LIFT` | fail |

Even HIT → **paper observe ballot only**.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stagec.py
```

Artifacts: `research/ops/FIN_BUY_QUALITY_STAGEC_*` · `repro/fin-buy-quality-stagec/`
