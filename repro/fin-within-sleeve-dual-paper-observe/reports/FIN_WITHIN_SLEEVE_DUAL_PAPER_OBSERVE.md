# FIN within-sleeve dual-paper (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **paper only** · Soft-Frozen **KEEP** · live wire **false**

| Book | Role |
|---|---|
| `FIN_EQUAL` | Equal-split Financial sleeve (control) |
| `FIN_RS_SOFT_TILT_EXDIV` | Stage C locked: RS soft-tilt + ex-div skip-buy |

Execution: capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

- MDD improve pp: 1.1116588036636177
- CAGR giveback pp: 1.1436922478520017
- Score: 0.5398126797376168

## Sealed vs BASE

- MDD improve pp: 2.722142747879508
- CAGR giveback pp: 1.6011368119133618
- Score: 1.921574341922827

## Tip FIN names

- BASE names w/ 張: 4
- CHAL names w/ 張: 4

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `repro/fin-within-sleeve-dual-paper-observe/`
