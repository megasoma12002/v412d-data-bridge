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
| `FIN_RS_SOFT_TILT_EXDIV` | 0.8926195082533894 | 1.0159269894833844 | 0.3846560135116972 |
| `MIX_L75` | 0.22403955244295615 | 0.2785842804694294 | 0.08474741220824145 |
| `KD_OPT` | 0.6664522064959488 | 0.266918547101902 | 0.5329929329449978 |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.5939580096014048 | 1.470104844284159 | 1.8589055874593252 |
| `MIX_L75` | 0.6862354707975027 | 0.4640827829000216 | 0.4541940793474919 |
| `KD_OPT` | 1.1616332365690596 | 0.38161132984990687 | 0.9708275716441062 |

## Tip FIN names (張)

- BASE: 4
- RS_EXDIV: 4
- MIX_L75: 4
- KD_OPT: 4

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `repro/fin-within-sleeve-dual-paper-observe/`
