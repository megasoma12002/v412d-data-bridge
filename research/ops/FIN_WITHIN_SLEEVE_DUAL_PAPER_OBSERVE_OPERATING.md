# FIN within-sleeve multi-paper (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **paper only** · Soft-Frozen **KEEP** · live wire **false**

| Book | Role |
|---|---|
| `FIN_EQUAL` | Equal-split Financial sleeve (control) |
| `FIN_RS_SOFT_TILT_EXDIV` | Stage C locked: RS soft-tilt + ex-div skip-buy |
| `MIX_L75` | Mix coexist: λ=0.75 EQUAL + (1−λ) RS_EXDIV |
| `KD_OPT` | KD optimal: `KD_APR15_MAY15_Klt30_T15` (Apr15–May15 K&lt;30.0 · T−15) |

Execution: capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 1.1116588036636177 | 1.1630172428419128 | 0.5301501822426613 |
| `MIX_L75` | 0.30259323641053104 | 0.35116300722883853 | 0.12701173279611178 |
| `KD_OPT` | 0.8066279142484367 | 0.3186621887207419 | 0.6472968198880658 |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.722142747879508 | 1.6452259928403157 | 1.89952975145935 |
| `MIX_L75` | 0.7668936128127024 | 0.5652499184702009 | 0.48426865357760196 |
| `KD_OPT` | 1.1789090714417805 | 0.46757526403025107 | 0.9451214394266549 |

## Tip FIN names (張)

- BASE: 4
- RS_EXDIV: 4
- MIX_L75: 3
- KD_OPT: 4

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `repro/fin-within-sleeve-dual-paper-observe/`
