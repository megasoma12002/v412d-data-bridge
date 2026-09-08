# FIN within-sleeve multi-paper (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **paper only** · Soft-Frozen **KEEP** · live wire **false**

| Book | Role |
|---|---|
| `FIN_EQUAL` | Equal-split Financial sleeve (control) |
| `FIN_RS_SOFT_TILT_EXDIV` | Stage C locked: RS soft-tilt + ex-div skip-buy |
| `MIX_L75` | Mix coexist: λ=0.75 EQUAL + (1−λ) RS_EXDIV |

Execution: capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 1.1116588036636177 | 1.1436922478520017 | 0.5398126797376168 |
| `MIX_L75` | 0.30259323641053104 | 0.34623771993473884 | 0.12947437644316162 |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.722142747879508 | 1.6011368119133618 | 1.921574341922827 |
| `MIX_L75` | 0.7668936128127024 | 0.5537598650254161 | 0.49001368029999437 |

## Tip FIN names (張)

- BASE: 4
- RS_EXDIV: 4
- MIX_L75: 3

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `repro/fin-within-sleeve-dual-paper-observe/`
