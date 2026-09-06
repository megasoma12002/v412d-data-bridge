# E45 Month-End Dual-Paper Runbook

Status: **OPERATING OBSERVE / PAPER OPS** — Soft-Frozen live Financial clip stays **[0.50, 0.95]**.  
Sleeve: Exact T+1 BASE Soft-Frozen early-stack vs **CHAL_E45_E3** (`E3_VOLTARGET_WINNER`).  
Parent: `E45_LIVE_STITCH_CHARTER.md` · `E45_DUAL_PAPER_OBSERVE_DESIGN.md` · `E45_DUAL_PAPER_OBSERVE_OPEN.md`  
Observe artifacts: `E45_DUAL_PAPER_OBSERVE.md` · `E45_MONTH_END_MONITOR.md`

## Cadence

1. On/after each month-end (or research refresh):
   ```bash
   python3 scripts/e45_dual_paper_ledgers.py
   python3 scripts/e45_month_end_monitor.py
   ```
   Or via pack:
   ```bash
   python3 scripts/ops_month_end_paper_pack.py              # monitor only
   python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow
   ```
2. Read `research/gaps/E45_MONTH_END_MONITOR.md`
3. File alerts into the debt board / ops note — **do not** edit Soft-Frozen

## Alert policy (paper)

| Window class | Windows | Policy |
|---|---|---|
| Dynamic | `ytd`, `trailing_1y` | ALERT if MDD worse or CAGR giveback > 3 pp; **PAUSE_REVIEW** if giveback > 5 pp |
| Structural | `heldout_2019_plus`, `sealed_2023_plus` | ALERT if MDD worse or giveback exceeds design baseline + 2 pp; **no structural PAUSE** (design-known giveback) |
| Display-only | `mtd`, `full` | Reported; not a stitch gate |

| Condition | Action |
|---|---|
| No dynamic alerts | Continue dual-paper **observe** |
| Dynamic PAUSE_REVIEW | Freeze stitch talk; Soft-Frozen unchanged; extend observe |
| Clean trailing alone | Still **not** a stitch license |

Design-known structural CAGR giveback (2026-09-05 design pack): heldout ≈ **5.65 pp**, sealed ≈ **9.40 pp**.

## Stitch (always blocked on this sleeve)

This observe sleeve **never** authorizes live stitch. Stitch would require:

1. Separate second human ACCEPT + stitch checklist PR
2. Soft-Frozen clip stays **[0.50, 0.95]** until that PR
3. No rewrite of `forward/e21` history

`stitch_blocked=true` / `cutover_blocked=true` are permanent for E45 month-end JSON.

## Parallel note

- BLEND_025 / FIN_CAP_50 / L4 dual-paper continue separately
- Do not conflate E45 observe PASS with Soft-Frozen CRITICAL promote or live stitch

## Label

`E45_MONTH_END_PAPER_RUNBOOK`
