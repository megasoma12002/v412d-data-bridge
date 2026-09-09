# Human Decision Register — Objective Priority

Date: 2026-09-05  
Authority: `research/STRATEGY_DEBT_BOARD.md` · map: `OPS_STATUS.md`  
Live Soft-Frozen Financial clip: **[0.60, 0.90]** (FINBAND ACCEPT 2026-09-09; was [0.50, 0.95])

## Decision rules (frozen)

1. Red gate → do **not** open a live cutover decision.  
2. Live change > paper observe (higher blast radius → later).  
3. If waiting reduces uncertainty cheaply, wait (trailing / sealed numbers).  
4. Structural fail ≠ “wait on the same lock” (FIN50 sealed CAGR).  
5. No charter → default **DEFER** (E45 / odd-lot / formal tax books).

## Explicit decisions (2026-09-05)

| Pri | Decision | Verdict | Binding effect |
|---:|---|---|---|
| 1 | Soft-Frozen live clip **[0.60, 0.90]** | **FLIPPED** (ACCEPT 2026-09-09 `FINBAND_F0.60-0.90`) | Was [0.50, 0.95]; note `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md` |
| 1b | Live starting capital | **500M** (ACCEPT 2026-09-09) | Was 3M restore; prior 15M then 3M; see `CAPITAL_500M_2026-09-09.md` |
| 2 | FIN_CAP_50 **static** live cutover | **REJECT for now** | Do not open cutover PR; do not retune FIN50 lock |
| 3 | Sealed-CAGR successor path | **BLEND_025 OPERATING OBSERVE** | Sole in-flight successor; observe ≠ promote |
| 4 | L4_DD_PATH live cutover | **DEFER** | No PR until checklist all-green (≥1 clean month-end, no YTD/1y PAUSE) |
| 5 | BLEND_025 → live | **NOT DECISION-READY** | Checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md`) but **NOT AUTHORIZED**; needs sustained trailing + human PR |
| 6a | Odd-lot default → `E22_v2s_tw` | **DONE** (2026-09-05) | #73+#74 merged; live `DEFAULT_BOOKS_VERSION = E22_v2s_tw`; Soft-Frozen KEEP; forward-only |
| 6b | Formal tax·receivable books | **ACCEPT charter** (2026-09-05) | Stage B sandbox OPEN; DEFAULT stays `E22_v2s_tw`; Soft-Frozen KEEP; promote needs later ballot |
| 6c | E45 live stitch | **ACCEPT stitch `BLEND_E45_A05`** (2026-09-09) | Second ACCEPT cast via「請都做」; wired forward-only in `e21`; note `E45_STITCH_ACCEPTED_BLEND_A05.md` |

## Research portfolio (2026-09-08)

| Decision | Verdict | Binding effect |
|---|---|---|
| Active research KEEP | **LOCKED** | FIN quartet (**`MIX_L75`** + **`KD_OPT`**) + E45 **`A05`/`C35`** + month-end gates |
| FIN within-sleeve live | **`KD_OPT` LIVE** (ACCEPT 2026-09-09) | `FIN_PRE_EXDIV_KD` forward-only; Soft-Frozen KEEP; note `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` |
| FIN autumn post-ex probe | **STOP** (2026-09-09) | small-search+dual no lift vs KD_OPT · `FIN_KD_AUTUMN_DUAL_SEASON.md` · live KD_OPT untouched |
| FIN hold posture | **LOCKED** (2026-09-09) | Maintain KD_OPT + month-end observe; no FIN micro-tune; 大勝 → clip or new-mechanism ballot · `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md` |
| 「大勝」ballots OPEN | **EXECUTED** (2026-09-09) | Clip observe OPEN + Class D FINBAND flip + E45 A05 stitch · `BIG_WIN_BALLOTS_OPEN.md` |
| Soft-Frozen clip flip | **`FINBAND_F0.60-0.90` LIVE** | `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md` |
| 「大勝」EXECUTED data re-run | **DONE** (2026-09-09) | `LIVE_STACK_RERUN.md` + `MONTH_END_PAPER_PACK.md` (--refresh-ledgers); NEW_LIVE held-out −0.68 tip ALERT vs pre-flip Soft-Frozen+KD |
| Remainder | **ARCHIVE** | Evidence retained; no new expansion; not primary agenda |

Detail: `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` · FIN posture: `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md`

### Register #6 sequential ballots

| Topic | Pack | Status |
|---|---|---|
| Odd-lot default → `E22_v2s_tw` | `ODD_LOT_PROMOTE_DECISION_PACK.md` | **DONE** — #73+#74 merged; DEFAULT=`E22_v2s_tw` |
| Tax / receivable formal books | `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `TAX_RECEIVABLE_CHARTER_DECISION_PACK.md` | **ACCEPT charter** — Stage B OPEN; no DEFAULT flip |
| E45 live stitch | `E45_LIVE_STITCH_CHARTER.md` · `E45_STAGE12_STATUS.md` · `E45_MDD_1316_NARRATIVE_RETIREMENT.md` · `E45_DUAL_PAPER_OBSERVE_OPEN.md` · `E45_STITCH_CHECKLIST.md` · `E45_BLEND025_OBSERVE_OPEN.md` | **ACCEPT charter** + **RETIRE unmatched handoff MDD narrative** + **OPEN observe** + **OPEN blend-α=0.25 observe**; stitch checklist **DRAFTED / NOT AUTHORIZED**; stitch still forbidden until second ACCEPT |

## Re-open triggers (only then re-agenda)

| Topic | Trigger to re-open human decision |
|---|---|
| L4 cutover | ≥1 clean month-end (no YTD/1y `PAUSE_REVIEW`) + `CUTOVER_CHECKLIST_L4` all YES |
| FIN50 static cutover | Go-live verify **not** `NOT_READY_SEALED_CAGR` **and** Gate E clean — else stay rejected |
| BLEND_025 promote | Sustained clean trailing on observe **and** cutover checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md` — **drafted 2026-09-05**, still NOT AUTHORIZED) |
| Soft-Frozen flip | Explicit human cutover PR only (never pack/monitor green alone) |
| Soft-Frozen clip **search** (paper) | `SOFT_FROZEN_CLIP_SEARCH_DECISION_PACK.md` — **ACCEPT charter** ✓ Stage B done; Soft-Frozen KEEP; Class D flip still separate |
| FIN within-sleeve live cutover | `CUTOVER_CHECKLIST_FIN_WITHIN_SLEEVE.md` · **ACCEPTED KD_OPT 2026-09-09** · `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` |
| Telecom within-sleeve alloc (paper) | `TELECOM_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md` — awaiting **ACCEPT charter**; Soft-Frozen KEEP |
| Odd-lot default | Human **ACCEPT promote** on `ODD_LOT_PROMOTE_DECISION_PACK.md` + checklist all YES + **par inventory VERIFIED** (`PAR_VALUE_LOOKUP_CHARTER.md`) |
| Tax / receivable books | Human **ACCEPT charter** then sandbox evidence + later promote PR |
| E45 stitch | Charter **ACCEPT** ✓ + retired MDD narrative **RETIRED** ✓ + dual-paper observe **OPEN** ✓ — V1–V6 PASS; **second** human ACCEPT still required for any live stitch PR |

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
