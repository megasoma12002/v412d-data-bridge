# FIN tip / sealed fill quality — Stage A (paper / observe)

Date: 2026-09-26  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · no live wire / no tip rewrite  
Parent: adj-OHLC fill audit (`LIVE_FILL_EXTREME_*`) + A–D deep dive  
Human: tip FIN 成交偏弱 → 單開 **FIN tip／sealed 成交品質** Stage A

Label: `FIN_TIP_SEALED_FILL_STAGEA_CHARTER_2026-09-26__OPEN__NO_LIVE_WIRE`

## Context

Tip adj audit (96 fills, Aug–Sep 2026): FIN BUY ±5d mean **~4.65%** vs TEL ~2.85% · all FIN `KD_OFFSEASON` · tip window no COOL/DH shrink.  
Full-history deep dive did **not** show KD off-season or CLIP_FIN_HI as structural fill defects.  
Question: is tip FIN weakness **sample noise**, or does **sealed'23+** also show FIN worse than peers?

## Question

On adj_close-scaled OHLC, for live twin fills:

1. How does **tip FIN** fill quality (n5 / n21 / T+1) compare to tip TEL / 0050?  
2. How does **sealed_2023_plus FIN** compare to sealed TEL / 0050 and to tip FIN?  
3. Within FIN tip + sealed: do `KD_OFFSEASON` / `CLIP_FIN_HI` / `DEFENSE_COOL` / side explain the gap?

## Non-actions

- Soft-Frozen clip flip · Exact T+1 change · tip rewrite  
- KD_OPT / COOL / TEL live retune · live wire · broker  

## Windows

| Window | Definition |
|---|---|
| `tip` | `forward/e21/fills.csv` executed tip ledger |
| `sealed_2023_plus` | FUSE+SELL_a75+COOL_c8 paper fills with `fill_date ≥ 2023-01-01` |

OHLC basis: **`adj_close`-scaled** (authoritative).

## Gates (observe)

| Gate | Pass |
|---|---|
| Tip gap | tip FIN ±5d mean − tip TEL ±5d mean ≥ **+0.50pp** |
| Sealed peer gap | sealed FIN ±5d − sealed TEL ±5d ≥ **+0.50pp** |
| Tip vs sealed | tip FIN ±5d − sealed FIN ±5d ≥ **+0.50pp** (tip uniquely bad) |

## Verdicts

| Verdict | Meaning |
|---|---|
| `FIN_TIP_SAMPLE` | tip gap vs TEL passes; sealed peer gap fails → tip-window noise |
| `FIN_SEALED_WEAK` | sealed FIN also ≥0.50pp worse than sealed TEL |
| `FIN_BOTH_WEAK` | tip peer gap + sealed peer gap both pass |
| `FIN_QUALITY_OK` | neither tip nor sealed peer gap reaches +0.50pp |
| `FIN_MECH_CONCENTRATED` | gap present but ≥70% of weak-bucket fills share one mechanism tag |

Even HIT-style weak → **paper observe only**; no live wire from Stage A.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_tip_sealed_fill_stagea.py
```

Artifacts: `research/ops/FIN_TIP_SEALED_FILL_STAGEA_*` · `repro/fin-tip-sealed-fill-stagea/`
