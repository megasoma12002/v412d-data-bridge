# E45 M2 BIL_FX dual-paper ledgers (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**

| Book | Role |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack ref |
| `M2_RELOC_BIL_FX_C35` | M2 relocate → `BIL_FX` @ c=0.35 |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: 2.5296553863856097
- CAGR giveback pp: 2.055310081167483
- Score: 1.5020003458018683

## Sealed vs BASE

- MDD improve pp: 1.1999153776515725
- CAGR giveback pp: 2.9838121441228216
- Score: -0.29199069440983827

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `repro/e45-m2-bil-fx-dual-paper-observe/`
