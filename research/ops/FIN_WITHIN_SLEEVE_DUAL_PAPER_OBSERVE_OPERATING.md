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
| `FIN_RS_SOFT_TILT_EXDIV` | 0.8926195082533894 | 0.9929627703258559 | 0.3961381230904615 |
| `MIX_L75` | 0.22403955244295615 | 0.2735289953181397 | 0.08727505478388631 |
| `KD_OPT` | 0.6664522064959488 | 0.25569550589275014 | 0.5386044535495738 |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.5939580096014048 | 1.4185661519003467 | 1.8846749336512314 |
| `MIX_L75` | 0.6862354707975027 | 0.4526735198653542 | 0.4598987108648256 |
| `KD_OPT` | 1.1616332365690596 | 0.3564446669667598 | 0.9834109030856797 |

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
