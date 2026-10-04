# TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbl** · Parents: 0kbk, 0kbj, 0kbi, 0kbf
Label: **MAJOR_DD_ATLAS_PARALLEL** · SOAK-SAFE parallel · **signal ≠ apply**
Tip SHA: `a5a9e6667bacff07fa98b9ce7fbab0897fc3b006`

## Question

Across **all major drawdowns** detectable on 0050 (2010+) and Soft/L4 NAV (2012-12+), how do cliffs vs grinds differ, and which detectors generalize across eras?

## Data

- Primary market: `data/telecom_0050_complete/0050_2010_latest_ohlcv.csv` (2010-01-04+)
- Optional TAIEX: `forward/e10s2/e10s2_taiex.csv` for corroboration
- Soft/L4: align-gap NAVs from 2012-12-04
- **No pre-2010 / GFC** series in-repo

## Design

- Detect peak→trough episodes depth ≥ **8%** and ≥ **10%**
- Classify CLIFF / GRIND / OTHER with **0kbk rules**: cliff_n≤20, grind_min≥40, vel_floor=0.004
- Named refs: 2011 EU/US · 2015 TW/CN · 2018Q4 · Mar2020 · 2022 bear · mid-2020 residual
- Per major (≥10%): detector IC/hit/recall (rvol20/63, atr, MA200 gap, dd63, fuse proxies, 0kbi AND champ when features exist)
- Cross-era score with/without Mar2020
- Verdicts: `MAJOR_DD_ATLAS_ROBUST` / `_PARTIAL` / `_ERA_SPECIFIC` / `_NO_EDGE`

## Hard constraints

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · no tip Soft promote · no year-oracle
- does **not** unlock soak freeze · no LIVE wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_major_dd_atlas_stagea.py`
