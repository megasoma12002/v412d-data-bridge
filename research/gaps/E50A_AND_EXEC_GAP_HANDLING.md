# Research: E50-A Overlay Gap (#5) + Execution Fidelity Gap (#6)

> **Note (2026-09-05):** Live DEFAULT books are now **`E22_v2s_tw`** (promoted).  
> Lines below that say “default still `E22_v2s` until promote” are **historical research context**.  
> Soft-Frozen clip unchanged; E45 live stitch remains DEFERRED.

Date: 2026-09-04  
Status: **RESEARCH ONLY** — no live promotion, no Soft-Frozen overwrite.  
Branch intent: decide *how to handle* both gaps without inventing frozen numbers.

---

## Executive verdict

| # | Gap | Handle how? | Do now? |
|---|---|---|---|
| **5** | E50-A overlay not connected | Keep **disconnected on live**; fix alpha gates in sandbox; only paper-stitch E16+overlay after gates clear | **Yes — research path**; **No live-wire** |
| **6** | Execution details simplified | Split **three labeled books**; land stock-share formal books (E22_v2s) first; defer pay-date/tax/lots to named challengers | **Yes — staged labeling + v2s**; no silent rewrite of history |

Long-term CAGR ≥20% / MDD ~10–15% remain **targets**, not current results. E16(+E22) alone cannot carry that target; E50-A cannot be “switched on” until it clears its own gates.

---

## Gap #5 — E50-A attack layer not connected

### Current state

Architecture (`FROZEN_STRATEGY_SPEC.md`):

```
Market → E16 Core → E18+E22 Execution → E50-A Alpha Overlay → E45 Crisis
```

Reality on `main` live path (`scripts/e21_forward_pipeline.py` + `forward/e21/`):

- E16 + Exact T+1 E18 run daily.
- E50-A is a **standalone research sleeve** (A0→A3→A3-R1), not capital allocated on top of E16.
- No approved overlay→E45 handoff.
- Combined four-layer engine: **not wired** (`E50_HANDOFF_VERIFICATION.md`).

### Why it is blocked (hard)

From reproduced R1 (`repro/e50a3r1-audit-20260903/outputs/a3r1/qc_status.json`):

| Gate | Result |
|---|---|
| Decision | `RESEARCH_ONLY` |
| `turnover_feasible_candidates` | **0** (ceiling 2.5% EXPERIMENTAL; selected train TO ~5.8%) |
| Validation CAGR vs PIT proxy | **14.95% vs 20.97%** (loses) |
| Validation MDD | **−33.5%** (far from 10–15% target) |
| Bootstrap ≥ 0.70 | fails (handoff: val boot ~0.26) |
| Governance class | EXPERIMENTAL model / thresholds — not SOFT_FROZEN |

Sealed window looks strong (CAGR ~48%) but **cannot promote** under the locked experimental gates + “no tuning on revealed sealed” policy.

### Soft gaps (not blockers to *study*, blockers to *live*)

- Early-stack core books exist (`e50_early_stack_combined_nav.py`) but are research.
- Sibling paper stacks (80/20 static mix ~15–17% CAGR in other branches) are EXPERIMENTAL and not on official live.
- E45 MDD −13.16% is **NOT_VERIFIED** (separate verification PR).

### Options

| Option | What | Invasiveness | Recommendation |
|---|---|---|---|
| **5A Docs honesty** | State clearly: live = E16(+exec); ≥20% not expected from core alone | Docs only | **Do** |
| **5B Sandbox stitch** | Paper `capital_core + capital_overlay` NAV beside E21; no state mutation | Challenger folder | **Do after** alpha gate work; keep `RESEARCH_ONLY` |
| **5C Alpha repair** | Address turnover / failure months / OOF stress **without** reading sealed for selection | EXPERIMENTAL research | **Primary workstream** |
| **5D Live-wire overlay into E21** | Allocate % to A3-R1 in `forward/e21` | Live | **Forbidden now** |

### Recommended handling path (#5)

1. **Accept “not connected” as correct** for live until `ELIGIBLE_FOR_E50_A4` (or successor) + explicit promotion.
2. **Do not** live-wire R1 (fails turnover + val proxy + MDD).
3. Next research (ordered):
   1. Finish turnover / held-out diagnosis already opened (`cursor/e50a3r1-turnover-diagnosis-d049`) — classify whether any candidate can meet TO without sealed peeking.
   2. Failure-signature study: when does R1 lose to proxy? (crisis vs EW months) — feeds overlay risk budget, not live weights.
   3. Only then: EXPERIMENTAL combined-book `E16 + overlay` paper NAV with **fixed** overlay fraction declared *before* looking at sealed (e.g. 80/20), Exact T+1, separate cash ledgers.
   4. Overlay→E45 handoff remains a **separate** SOFT_FROZEN_CRITICAL challenger; do not invent handoff thresholds.
4. Promotion bar stays: beat proxy on val **and** sealed, bootstrap gates if still used, TO feasible, governance PR + approval.

### What “success” looks like (technical)

- Overlay sleeve: `turnover_feasible_candidates > 0` under predeclared ceiling **or** ceiling itself revised via new EXPERIMENTAL version id (not silent edit).
- Combined paper book: OOS report with core-only vs core+overlay deltas, cost stress, crisis windows.
- Live: only after promotion path completes — never “temporary” allocation in E21.

---

## Gap #6 — Execution details still simplified

### Current state

Spec Layer-2 wants: ex → receivable → payment → tax → odd lot → fill realism.  
Implemented (partial):

| Item | Live E21 | Research early-stack | Ledger data |
|---|---|---|---|
| Cash dividend | **Not applied** | Credit on **cash_ex_date** | Complete (payment dates filled) |
| Stock dividend | **Not applied** | Optional share `×(1+元/股/10)` on stock ex | Complete |
| Payment-date cash | Unused | Unused (delivery only) | Complete; E22_v3 H1 sandbox elsewhere |
| Sell tax | Yes (stock 30bp / ETF 10bp) | Yes | — |
| Dividend tax | No | No (TAX0) | — |
| Board lot 1000 | No (1-share `int`) | No | — |
| Fractionals | N/A | `int(pos)` on sells → stranded dust | — |

Related work already in flight / done on sibling PRs:

- Stock-aware formal books **E22_v2s** (PR #30) — recommended formal raw-price books.
- Historical recompute side-by-side (~11.25% vs ~13.78% CAGR).
- E22_v3 H1 payment-date (PR #22) — interesting, **no promote**.

### Gap inventory (severity)

| ID | Gap | Severity | Why it matters |
|---|---|---|---|
| 6.1 | Cash on ex-date, no receivable | Med | Cash available too early vs custody |
| 6.2 | Payment date unused | Low–Med | Ops liquidity; thin research util lift |
| 6.3 | No dividend withholding tax | Med (after-tax) | Live net cash ≠ sim |
| 6.4 | Stock shares missing on official/live | **High** (raw TR) | Understates NAV ~+2.5 pp CAGR in research |
| 6.5 | Fractional shares stranded | Med | Dust accumulates; sells floor with `int` |
| 6.6 | No TW 整股/零股 | Med–High live | Capacity / fill quality |
| 6.7 | Live E21 still no E22 at all | **High** label risk | Research CAGR ≠ live ledger |

### Options

| Gap | Research proxy | Formal handling |
|---|---|---|
| 6.4 Stock | Already computed | Merge/adopt **E22_v2s**; preserve **E22_v2** cash-only label; cutover-forward only |
| 6.7 Live wire | — | Wire E22_v2s into E21 from cutover (idempotent keys); **do not** rewrite history |
| 6.1–6.2 Timing | Keep ex-date for TR continuity | Optional receivable books or `E22_v3_*` pay clock — new version id only |
| 6.3 Div tax | Publish 0/10/20% haircuts | Named after-tax books if needed for ops |
| 6.5–6.6 Lots | Floor + cash-in-lieu sensitivity; 1000-lot challenger | E18 challenger folder; Exact T+1 unchanged |

### Recommended handling path (#6)

**Stage A — Label (now)**  
Publish three parallel identities (no behavior fight):

1. `E22_v2` — cash-only ex-date (preserved baseline ~11.2%)  
2. `E22_v2s` — cash + stock shares on ex (formal raw TR books ~13.8%)  
3. `E22_v3_*` — payment-date / tax / receivable sandboxes (not promoted)

**Stage B — Formal stock books (next code)**  
- Land E22_v2s module + E21 forward default (PR #30 lineage).  
- Historical research side-by-side already answers “must we recompute?” → research yes, live history no.

**Stage C — Fractional + board-lot challenger**  
- **6.5 DONE (named):** `E22_v2s_tw` = floor + par NT$10 CIL (see `research/e22/GAP65_ODD_LOT_CLOSEOUT.md`). Default still `E22_v2s` until promote.  
- Board-lot 1000: E18 capacity challenger only (TW 零股 allows 1–999).

**Stage D — Pay-date / tax only if ops ask**  
- H1 showed interesting but fragile util; keep sandbox.  
- After-tax haircuts as sensitivity tables beside formal pre-tax books.

### Exact T+1 / Soft-Frozen constraints

- Clock stays: signal T → fill next open.  
- Never edit E22_v2 semantics in place — new version ids only.  
- Never rewrite immutable historical `forward/e21/nav.csv` rows for backfilled dividends.

---

## Joint roadmap (what to do in order)

| Step | Addresses | Action | Outcome artifact |
|---|---|---|---|
| 1 | #5 | Document live = core-only; ≥20% not claimed | this report |
| 2 | #6 | Merge/adopt E22_v2s formal books + labels | PR #30 / accounting module |
| 3 | #6 | Wire E21 forward dividends cutover-only | `dividends_applied.csv` |
| 4 | #5 | Complete R1 turnover / held-out diagnosis | diagnosis PR |
| 5 | #5 | Failure-signature → overlay risk budget (paper) | research note |
| 6 | #6 | Fractional + 1000-lot E18 challenger | repro sandbox — **6.5 CLOSED** as `E22_v2s_tw` named (par CIL); board-lot still challenger |
| 7 | #5 | Paper combined book (fixed overlay %) predeclared | early-stack sibling |
| 8 | #5+#6 | Promotion review only after gates + approval | governance |

**Stop conditions**

- Do not allocate live overlay capital while `RESEARCH_ONLY`.  
- Do not treat sealed outperformance as promotion.  
- Do not replace E22_v2 with pay-date books without a new version.  
- Do not invent E45 handoff cuts or revive unverified −13.16% MDD.

---

## Key references

- `E50_HANDOFF_VERIFICATION.md`, `E50-A3-R1_TODO.md`, `research/e50a3r1/README.md`
- `repro/e50a3r1-audit-20260903/outputs/a3r1/qc_status.json`
- `FROZEN_STRATEGY_SPEC.md` Layer 2–3, `FROZEN_GOVERNANCE.md`
- `research/e22/DIVIDEND_LEDGER_COMPLETE.md`, `STOCK_DIVIDEND_LEDGER.md`
- `research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md` (detail companion)
- Sibling PRs: #19 turnover diagnosis, #22 E22_v3 H1, #30 E22_v2s, #31 E45 MDD verify
