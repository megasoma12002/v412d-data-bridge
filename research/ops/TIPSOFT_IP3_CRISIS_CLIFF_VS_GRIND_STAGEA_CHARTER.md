# TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbk** · Parents: 0kbj, 0kbi, 0kbh, 0kbf
Label: **CLIFF_GRIND_PARALLEL** · SOAK-SAFE parallel · **signal ≠ apply**
Tip SHA: `263fb5cfadbb4f05ff05d7de43ee830ee2e3b462`

## Question

How do stress **regimes** differ — short cliffs (急殺) vs long grinds (長期跌) — in (a) shape metrics, (b) which lag-1 detectors fire, (c) whether size overlays / DD_SWITCH-like cash gates help held vs MDD?

## Taxonomy

- Auto-detect drawdown episodes on Soft/L4 NAV + 0050 (depth ≥ 0.08 / grid (0.08, 0.1))
- **CLIFF** if time-to-trough ≤ N (grid (10, 15, 20)) AND velocity ≥ 0.004 (fraction/day)
- **GRIND** if ttm ≥ (40, 60) with similar depth
- Manual ref tags: Mar2020 cliff · 2015 · 2018Q4 · mid/late 2020 residual (0kb4)

## Metrics / verdict

- Shape table: depth · duration · velocity · recovery · V/L shape
- Detector lift by regime (0kbh singles + 0kbi AND champ): IC/hit/recall within CLIFF vs GRIND
- Illustrative cash-gate CF only (not promote)
- `CLIFF_GRIND_SPLIT_HIT` / `_WEAK` / `_NO_SPLIT`

## Hard constraints

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · no tip Soft promote · no year-oracle
- does **not** unlock soak freeze · no LIVE wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_cliff_vs_grind_stagea.py`
