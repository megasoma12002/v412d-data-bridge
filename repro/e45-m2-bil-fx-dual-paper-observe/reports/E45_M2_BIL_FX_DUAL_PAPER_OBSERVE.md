# E45 M2 BIL_FX dual-paper ledgers (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**

| Book | Role |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack ref |
| `M2_RELOC_BIL_FX_C35` | M2 relocate → `BIL_FX` @ c=0.35 |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: 2.308622276182526
- CAGR giveback pp: 2.0426327897418384
- Score: 1.2873058813116067

## Sealed vs BASE

- MDD improve pp: -0.6554581461998499
- CAGR giveback pp: 3.1087957269206212
- Score: -2.2098560096601605

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `repro/e45-m2-bil-fx-dual-paper-observe/`
