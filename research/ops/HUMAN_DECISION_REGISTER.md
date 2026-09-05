# Human Decision Register — Objective Priority

Date: 2026-09-05  
Authority: `research/STRATEGY_DEBT_BOARD.md` · map: `OPS_STATUS.md`  
Live Soft-Frozen Financial clip: **[0.50, 0.95]**

## Decision rules (frozen)

1. Red gate → do **not** open a live cutover decision.  
2. Live change > paper observe (higher blast radius → later).  
3. If waiting reduces uncertainty cheaply, wait (trailing / sealed numbers).  
4. Structural fail ≠ “wait on the same lock” (FIN50 sealed CAGR).  
5. No charter → default **DEFER** (E45 / odd-lot / formal tax books).

## Explicit decisions (2026-09-05)

| Pri | Decision | Verdict | Binding effect |
|---:|---|---|---|
| 1 | Soft-Frozen live clip **[0.50, 0.95]** | **KEEP** | No auto-flip; any change = dedicated human PR |
| 2 | FIN_CAP_50 **static** live cutover | **REJECT for now** | Do not open cutover PR; do not retune FIN50 lock |
| 3 | Sealed-CAGR successor path | **BLEND_025 OPERATING OBSERVE** | Sole in-flight successor; observe ≠ promote |
| 4 | L4_DD_PATH live cutover | **DEFER** | No PR until checklist all-green (≥1 clean month-end, no YTD/1y PAUSE) |
| 5 | BLEND_025 → live | **NOT DECISION-READY** | Checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md`) but **NOT AUTHORIZED**; needs sustained trailing + human PR |
| 6 | E45 / odd-lot default / formal tax·receivable | **DEFER** | New charter required before any work toward live |

## Re-open triggers (only then re-agenda)

| Topic | Trigger to re-open human decision |
|---|---|
| L4 cutover | ≥1 clean month-end (no YTD/1y `PAUSE_REVIEW`) + `CUTOVER_CHECKLIST_L4` all YES |
| FIN50 static cutover | Go-live verify **not** `NOT_READY_SEALED_CAGR` **and** Gate E clean — else stay rejected |
| BLEND_025 promote | Sustained clean trailing on observe **and** cutover checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md` — **drafted 2026-09-05**, still NOT AUTHORIZED) |
| Soft-Frozen flip | Explicit human cutover PR only (never pack/monitor green alone) |
| E45 / odd-lot | New charter accepted |

## Non-decisions (ops wait — no strategy vote needed)

- Next weekday forward → run `POST_FORWARD_E22_VERIFY_RUNBOOK.md`; persist live `e22_*` evidence; re-run Gap6 KPI  
- Grow live history toward ≥~60 sessions  
- Calendar month-end pack re-run (L4 / FIN50 / BLEND_025 trailing)

## Claim policy

Live may not claim numeric CAGR/MDD target badges until a cutover PR merges.  
See `research/ops/LIVE_CLAIM_TARGET_POLICY.md`.

## How to run a future strategy update

End-to-end stage map (classify → charter → paper → observe → register gate → checklist → human cutover PR → post-QC):  
`research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`.

This register remains the **only** place that re-opens live cutover agendas; the SOP does not add new verdicts.

## Label

`HUMAN_DECISION_REGISTER_2026-09-05`
