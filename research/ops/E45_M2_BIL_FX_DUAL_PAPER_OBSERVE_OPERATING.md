# E45 M2 BIL_FX dual-paper ledgers (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**

| Book | Role |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack ref |
| `M2_RELOC_BIL_FX_C35` | M2 relocate → `BIL_FX` @ c=0.35 |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: 2.223693801227644
- CAGR giveback pp: 2.5759489529906476
- Score: 0.9357193247323203

## Sealed vs BASE

- MDD improve pp: 2.288363517446379
- CAGR giveback pp: 3.303639538617409
- Score: 0.6365437481376746

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `repro/e45-m2-bil-fx-dual-paper-observe/`
