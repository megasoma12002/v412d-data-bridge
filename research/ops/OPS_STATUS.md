# Ops Status — One-Page Map

Date: 2026-09-05 (Phase 1 cadence wired)  
Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**

## What is live (only this)

| Item | Value |
|---|---|
| Stack | **E16 + Exact T+1 E18 + E22_v2s** |
| Path | `forward/e21/` |
| Clip | Financial **[0.50, 0.95]** via `scripts/e16_soft_frozen_base.py` |
| Daily job | `.github/workflows/v412f-forward-paper.yml` (weekdays) |
| QC smoke | `.github/workflows/e21-live-qc-smoke.yml` |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

**Not live:** E45, E50-A overlay, FIN_CAP_50, L4_DD_PATH, Track A/B, E6/E9/E10 shadows.

## Paper sleeves (observe only)

| Sleeve | Status | Cutover |
|---|---|---|
| FIN_CAP_50 | Dual-paper OPERATING | **`NOT_READY_SEALED_CAGR` / FROZEN** |
| L4_DD_PATH_08_50 | Held-out PASS; dual-paper OPERATING | **FROZEN** (YTD PAUSE_REVIEW asof 2026-09-04) |
| Track A S9A1 | KEEP (paper/monitor) | N/A — not a live cutover path |
| Track B S1 | STOP | Closed |

## Cadence (Phase 1)

| Cadence | How |
|---|---|
| Daily live | Existing `v412f-forward-paper` weekday job |
| Live QC smoke | `e21-live-qc-smoke` on PR/push touching live path, or `workflow_dispatch` |
| Month-end paper pack | `ops-month-end-paper-pack` — `workflow_dispatch` (preferred) or cron 1st of month UTC |
| Live↔paper recon | Included in month-end pack; also `python3 scripts/e21_live_vs_paper_recon.py` |

## Commands (operator cheat-sheet)

```bash
# Live QC only (no data rebuild)
python3 scripts/e21_qc.py --state-dir forward/e21

# One-button month-end paper pack (monitors + recon; Soft-Frozen untouched)
python3 scripts/ops_month_end_paper_pack.py

# Slow path: also rebuild dual-paper ledgers first
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers

# Live ↔ Soft-Frozen paper BASE recon only
python3 scripts/e21_live_vs_paper_recon.py
```

## Authority

1. **Cutover / Now-Next:** `research/STRATEGY_DEBT_BOARD.md`  
2. **Ops map (this page):** `research/ops/OPS_STATUS.md`  
3. **Convergence plan:** `research/ops/OPS_CONVERGENCE_CHARTER.md`  
4. **Class ≠ live:** `FROZEN_GOVERNANCE.md` § Soft-Frozen class  

## Hard rules

- No auto Soft-Frozen flip  
- Dual-paper / held-out PASS ≠ cutover  
- Never rewrite `forward/e21` history  
- MTD annualized CAGR is **display-only**, not a cutover gate  
- Strategy merge (L4 / FIN50 / alpha / E45) stays **human cutover-gated** — not part of this cadence  
