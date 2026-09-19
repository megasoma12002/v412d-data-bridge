# ACCEPT — Paper simulate_core fill policy aligns to live skip

Status: **ACCEPTED** (this PR)  
Date: 2026-09-19  
Soft-Frozen live path: **unchanged** (already skips) · research NAV: **may change**

## Ballot

> `ACCEPT paper/live fill align: simulate_core underfunded BUY skips (afford < orig_q) and requeues — same as live_fill_core; no Soft-Frozen cutover`

## What changes

| Path | Before | After |
|---|---|---|
| Live `live_fill_core._paper_fill_rows` | skip when `afford < orig_q` | unchanged |
| Research `e50.simulate_core` | partial-fill shrink `q` | **skip + keep pending** when `afford < orig_q` |

## Effects

- Dual-paper / month-end / MDD research NAVs may drift on cash-tight days.
- Refresh observe ledgers under existing observe posture; do not treat as live cutover.
- Soft-Frozen `forward/e21` fills policy already matched — no live ledger rewrite.

## Non-goals

- Does **not** enable `broker_live_write_accepted` or `API_WIRED`
- Does **not** reopen E45 A05 stitch

Label: `ACCEPT_2026-09-19_PAPER_LIVE_FILL_SKIP_ALIGN`
