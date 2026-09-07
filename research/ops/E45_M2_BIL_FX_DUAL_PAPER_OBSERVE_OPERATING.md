# E45 M2 BIL_FX dual-paper ledgers (OPERATING OBSERVE)

**Status:** `OPERATING_OBSERVE` — **OPERATING (paper only)**

| Book | Role |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack ref |
| `M2_RELOC_BIL_FX_C50` | M2 relocate → `BIL_FX` @ c=0.5 |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: 2.9585299388856345
- CAGR giveback pp: 3.431416298385259
- Score: 1.242821789693005

## Sealed vs BASE

- MDD improve pp: 2.652963145586207
- CAGR giveback pp: 4.755390094477008
- Score: 0.27526809834770294

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `repro/e45-m2-bil-fx-dual-paper-observe/`
