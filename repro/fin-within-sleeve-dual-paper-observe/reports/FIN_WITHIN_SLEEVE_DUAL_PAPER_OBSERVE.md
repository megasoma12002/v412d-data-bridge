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
| `FIN_RS_SOFT_TILT_EXDIV` | 0.8926195082533894 | 0.9789885162456935 | 0.4031252501305427 |
| `MIX_L75` | 0.22403955244295615 | 0.27106226954756174 | 0.08850841766917528 |
| `KD_OPT` | 0.6664522064959488 | 0.2516306978320504 | 0.5406368575799236 |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.5939580096014048 | 1.385814366849769 | 1.9010508261765202 |
| `MIX_L75` | 0.6862354707975027 | 0.4464184145289485 | 0.46302626353302845 |
| `KD_OPT` | 1.1616332365690596 | 0.34700163204750556 | 0.9881324205453068 |

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
