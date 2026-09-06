# E45 Dual-Sleeve Long Monitor Dashboard

Generated: `2026-09-06T03:04:19.457735+00:00`
Status: **PAPER DASHBOARD** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**.
Operating observe: **CHAL_E45_E3** + **BLEND_E45_A25**. Paper companion **A10** is NOT an OPEN observe sleeve.

## Operating observe — latest alerts

- CHAL_E45_E3 asof `2026-09-04`:
  - ALERT: CHAL_E45_E3 ytd CAGR giveback > 3.0 pp (paper)
  - PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
  - ALERT: CHAL_E45_E3 trailing_1y CAGR giveback > 3.0 pp (paper)
  - PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
- BLEND_E45_A25 asof `2026-09-04`:
  - ALERT: BLEND_E45_A25 ytd CAGR giveback > 3.0 pp (paper)
  - PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk
  - ALERT: BLEND_E45_A25 trailing_1y CAGR giveback > 3.0 pp (paper)
  - PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no stitch talk

## Operating observe — window table

| Sleeve | Window | MDD Δpp | Giveback pp |
|---|---|---:|---:|
| CHAL_E45_E3 | mtd | +0.00 | +1012.81 |
| CHAL_E45_E3 | ytd | +7.23 | +23.23 |
| CHAL_E45_E3 | trailing_1y | +7.23 | +20.49 |
| CHAL_E45_E3 | sealed_2023_plus | +4.90 | +9.40 |
| CHAL_E45_E3 | heldout_2019_plus | +1.88 | +5.65 |
| CHAL_E45_E3 | full | +1.88 | +2.99 |
| BLEND_E45_A25 | mtd | +0.00 | +728.79 |
| BLEND_E45_A25 | ytd | +5.94 | +11.55 |
| BLEND_E45_A25 | trailing_1y | +5.94 | +11.69 |
| BLEND_E45_A25 | sealed_2023_plus | +5.13 | +4.36 |
| BLEND_E45_A25 | heldout_2019_plus | +0.63 | +2.83 |
| BLEND_E45_A25 | full | +0.63 | +1.38 |
| BLEND_E45_A05 | mtd | +0.00 | +391.32 |
| BLEND_E45_A05 | ytd | +2.78 | +4.87 |
| BLEND_E45_A05 | trailing_1y | +2.78 | +5.17 |
| BLEND_E45_A05 | sealed_2023_plus | +2.78 | +1.42 |
| BLEND_E45_A05 | heldout_2019_plus | +0.70 | +0.96 |
| BLEND_E45_A05 | full | +0.70 | +0.42 |

## Paper companion BLEND_E45_A10 (asof 2026-09-04) — NOT OBSERVE

| Window | MDD Δpp | Giveback pp | Flag |
|---|---:|---:|---|
| ytd | +3.65 | +6.56 | **PAUSE_REVIEW** |
| trailing_1y | +3.65 | +6.93 | **PAUSE_REVIEW** |
| heldout_2019_plus | +0.80 | +1.51 | **n/a** |
| sealed_2023_plus | +3.65 | +2.12 | **n/a** |

## Read-through

1. Keep FULL vs A25 observe on month-end cadence; both feed stitch gates.
2. A10 companion is research-only after low-α deep-dive; **no OPEN ballot** here.
3. Dashboard does not authorize stitch.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED
- Observe OPEN sleeves unchanged (FULL + A25 only)

## Reproduce

```bash
python3 scripts/e45_dual_sleeve_monitor_dashboard.py
```

