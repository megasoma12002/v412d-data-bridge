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
| 6a | Odd-lot default → `E22_v2s_tw` | **DONE** (2026-09-05) | #73+#74 merged; live `DEFAULT_BOOKS_VERSION = E22_v2s_tw`; Soft-Frozen KEEP; forward-only |
| 6b | Formal tax·receivable books | **ACCEPT charter** (2026-09-05) | Stage B sandbox OPEN; DEFAULT stays `E22_v2s_tw`; Soft-Frozen KEEP; promote needs later ballot |
| 6c | E45 live stitch | **ACCEPT charter** + **RETIRE −13.16%** + **OPEN dual-paper observe** (2026-09-05) | Stage 1–3 DONE; observe **OPERATING**; **V1–V6 PASS**; Soft-Frozen CRITICAL KEEP; live/stitch still **FORBIDDEN** until **second** stitch ACCEPT; board `E45_STAGE12_STATUS.md`; open `E45_DUAL_PAPER_OBSERVE_OPEN.md` |

### Register #6 sequential ballots

| Topic | Pack | Status |
|---|---|---|
| Odd-lot default → `E22_v2s_tw` | `ODD_LOT_PROMOTE_DECISION_PACK.md` | **DONE** — #73+#74 merged; DEFAULT=`E22_v2s_tw` |
| Tax / receivable formal books | `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `TAX_RECEIVABLE_CHARTER_DECISION_PACK.md` | **ACCEPT charter** — Stage B OPEN; no DEFAULT flip |
| E45 live stitch | `E45_LIVE_STITCH_CHARTER.md` · `E45_STAGE12_STATUS.md` · `E45_MDD_1316_NARRATIVE_RETIREMENT.md` · `E45_DUAL_PAPER_OBSERVE_OPEN.md` | **ACCEPT charter** + **RETIRE −13.16%** + **OPEN observe**; **V1–V6 PASS**; stitch still forbidden until second ACCEPT |

## Re-open triggers (only then re-agenda)

| Topic | Trigger to re-open human decision |
|---|---|
| L4 cutover | ≥1 clean month-end (no YTD/1y `PAUSE_REVIEW`) + `CUTOVER_CHECKLIST_L4` all YES |
| FIN50 static cutover | Go-live verify **not** `NOT_READY_SEALED_CAGR` **and** Gate E clean — else stay rejected |
| BLEND_025 promote | Sustained clean trailing on observe **and** cutover checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md` — **drafted 2026-09-05**, still NOT AUTHORIZED) |
| Soft-Frozen flip | Explicit human cutover PR only (never pack/monitor green alone) |
| Odd-lot default | Human **ACCEPT promote** on `ODD_LOT_PROMOTE_DECISION_PACK.md` + checklist all YES + **par inventory VERIFIED** (`PAR_VALUE_LOOKUP_CHARTER.md`) |
| Tax / receivable books | Human **ACCEPT charter** then sandbox evidence + later promote PR |
| E45 stitch | Charter **ACCEPT** ✓ + −13.16% **RETIRED** ✓ + dual-paper observe **OPEN** ✓ — V1–V6 PASS; **second** human ACCEPT still required for any live stitch PR |

## Non-decisions (ops wait — no strategy vote needed)

- Next weekday forward → run `POST_FORWARD_E22_VERIFY_RUNBOOK.md`; persist live `e22_*` evidence; re-run Gap6 KPI  
- Grow live history toward ≥~60 sessions  
- Calendar month-end pack re-run (L4 / FIN50 / BLEND_025 / E45 dual-paper trailing)

## Claim policy

Live may not claim numeric CAGR/MDD target badges until a cutover PR merges.  
See `research/ops/LIVE_CLAIM_TARGET_POLICY.md`.

## How to run a future strategy update

End-to-end stage map (classify → charter → paper → observe → register gate → checklist → human cutover PR → post-QC):  
`research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`.

This register remains the **only** place that re-opens live cutover agendas; the SOP does not add new verdicts.

## Label

`HUMAN_DECISION_REGISTER_2026-09-05`
