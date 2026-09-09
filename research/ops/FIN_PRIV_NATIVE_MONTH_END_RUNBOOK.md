# 民營 Native Month-End Dual-Paper Runbook

Status: **OPERATING OBSERVE / PAPER OPS**  
Soft-Frozen live Financial clip: **[0.60, 0.90] FINBAND KEEP** (公股 R1)  
Live Financial within-sleeve: **公股 `KD_OPT` KEEP** · live wire **false**  
Books: `PRIV_EQUAL` ∥ `PRIV_KD_MAY_Klt25_T15`  
Authority: `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN.md` · checklist `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST.md` · posture `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md`

## Cadence (fixed)

1. On/after each calendar month-end (or research refresh when market tip advances):

   ```bash
   python3 scripts/e16_fin_priv_native_dual_paper_ledgers.py
   python3 scripts/e16_fin_priv_native_month_end_monitor.py
   ```

   Or via pack:

   ```bash
   python3 scripts/ops_month_end_paper_pack.py                 # monitors (incl. fin_priv_native)
   python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow; refreshes priv ledgers too
   ```

2. Read `research/ops/FIN_PRIV_NATIVE_MONTH_END_MONITOR.md` (+ `.json`).
3. File tip / structural alerts into debt board / ops note — **do not** edit Soft-Frozen or live e21.
4. If tip PAUSE_REVIEW persists ≥2 month-ends **or** structural ALERT fires → open / refresh status ballot (below). Do **not** auto-promote.

## Alert policy (paper)

Alert windows: **`ytd`**, **`trailing_1y`**, **`heldout_2019_plus`**, **`sealed_2023_plus`**.  
`mtd` is reported only (not a status gate).

| Condition | Action |
|---|---|
| No alerts | Continue dual-paper **KEEP OBSERVE** |
| MDD worse than `PRIV_EQUAL` (tip window) | Tip **ALERT** — extend observe; no live talk |
| CAGR giveback &gt; 3 pp (YTD / 1y) | Tip **ALERT** — extend observation |
| CAGR giveback &gt; 5 pp (YTD / 1y) | **PAUSE_REVIEW** — freeze any escalate-to-live talk; Soft-Frozen unchanged |
| Held-out / sealed giveback &gt; design + 2 pp buffer | Structural **ALERT** — status ballot toward stricter paper or STOP |
| Clean trailing alone | Still **not** a live-wire license |

Design giveback targets (from monitor SSOT): held-out **0.5** pp · sealed **0.8** pp · buffer **2.0** pp.

## Tip / structural watch list

| Metric | Where | Pass heuristic |
|---|---|---|
| YTD giveback / MDD↑ | monitor `ytd` | giveback ≤ 3 pp · MDD↑ ≥ 0 |
| Trailing 1y giveback / MDD↑ | monitor `trailing_1y` | same |
| Held-out score | monitor `heldout_2019_plus` | score &gt; 0 (design ~+0.63) |
| Sealed score | monitor `sealed_2023_plus` | score ≥ ~0 (report-only; design ~flat) |
| Rel NAV tip | monitor windows | informational |

## Status ballot (observe-only — not live)

When cadence says escalate, use:

- `research/ops/FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md`

Choices are **KEEP OBSERVE** · **stricter paper** · **STOP observe**.  
**Not** on the ballot: Soft-Frozen flip · live e21 expand · 4-sleeve Class D · live 公股 KD retune.

## Cutover / live wire (always blocked on this sleeve)

This observe sleeve **never** authorizes live universe expand or Soft-Frozen membership change.

Blocked path stub: `CUTOVER_CHECKLIST_FIN_PRIV_NATIVE.md` — **NOT AUTHORIZED / BLOCKED**.

Any future live path would need:

1. New charter + Stage A tip-clean **and** held-out &gt; 0 vs **live 公股 KD** (prior PRIV-replace / dual / 4-sleeve all STOP)
2. Dedicated human ACCEPT + cutover PR  
3. Soft-Frozen KEEP until that PR  
4. No rewrite of `forward/e21` history

## Parallel note

- Live 公股 FIN within-sleeve observe continues separately (`FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md`)  
- Do **not** conflate 民營 paper PASS with Soft-Frozen 4-sleeve or live KD promote  
- PRIV-replace / dollar-split / 4-sleeve research remain **STOP**

## First cadence stamp

| Field | Value |
|---|---|
| As-of | **2026-09-09** |
| Alerts | **none** |
| Held-out score | **+0.625** |
| Pack wire | `#170` |

## Label

`FIN_PRIV_NATIVE_MONTH_END_PAPER_RUNBOOK_2026-09-09`
