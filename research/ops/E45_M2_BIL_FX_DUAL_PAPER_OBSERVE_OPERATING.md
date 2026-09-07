# E45 M2 BIL_FX dual-paper ledgers (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**

| Book | Role |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack ref |
| `M2_RELOC_BIL_FX_C35` | M2 relocate → `BIL_FX` @ c=0.35 |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: 2.619027821648412
- CAGR giveback pp: 2.226804669213278
- Score: 1.505625487041773

## Sealed vs BASE

- MDD improve pp: 1.5267479674788587
- CAGR giveback pp: 3.157810884254153
- Score: -0.05215747464821785

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `repro/e45-m2-bil-fx-dual-paper-observe/`
