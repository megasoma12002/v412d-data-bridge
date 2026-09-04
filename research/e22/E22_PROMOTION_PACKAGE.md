# E22 Promotion Package — Wire Dividends into Official Exec Path

Date: 2026-09-04  
Challenger ID: `E22_OFFICIAL_PATH_CASH_EX_CREDIT`  
Proposed new version label (if approved): **`E22_v2_CASH_EX_OFFICIAL_PATH`**  
Status: **`AWAITING_EXPLICIT_HUMAN_APPROVAL`** — not promoted

Follows `FROZEN_GOVERNANCE.md` §2 promotion path. Does **not** edit E21 in place.

---

## 1. Hypothesis

Wiring **cash dividend credits on `cash_ex_date`** into the official Exact T+1 execution loop (same membership / fees / fills as E21) improves economic NAV versus the current live path that omits dividend cashflows, without weakening HARD_FROZEN causality.

---

## 2. Frozen baseline (preserved)

| Object | Location |
|---|---|
| Official live loop | `scripts/e21_forward_pipeline.py` |
| Official ledgers | `forward/e21/` (untouched) |
| Current E22 research ledger | `data/dividend_events/e22_dividend_events.csv` |
| Baseline NAV (no E22 cash in loop) | E21 live + early-stack `E16_E18` book |

---

## 3. Challenger (separate folder)

| Object | Location |
|---|---|
| Script | `scripts/e22_challenger_forward_pipeline.py` |
| Paper ledgers | `forward/e22_challenger/` |
| Full-history economics | `repro/early-stack-combined-nav-20260904/` (`E16_E18` vs `E16_E18_E22`) |

Mechanism: after Exact T+1 open fills, credit `shares × cash_dividend` on `cash_ex_date` into cash. Same orders / fees / slippage as E21.

---

## 4. Side-by-side evidence

### 4a. Full-history reconstructed E16 book (primary economics)

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| E16_E18 (baseline) | 7.22% | −22.77% | −0.0417 |
| E16_E18_E22 (challenger) | 11.19% | −22.11% | 0.0013 |

- CAGR lift: **+3.97 pp**
- MDD change: **+0.66 pp** (slightly better)
- Exact T+1: OK in sandbox meta

### 4b. Official-path-shaped paper loop (2026-07-01 → 2026-09-03)

| Check | Result |
|---|---|
| QC | **PASS** (`forward/e22_challenger/qc_status.json`) |
| Exact T+1 fills | **PASS** |
| Sessions | 46 |
| Dividend cash credited | **~84,353** on 3M capital |
| Days with credit | Aug 11–13 2026 (FIN names) + Jul telecom/0050 window |

Note: E21 live started **2026-08-24** (after Aug ex-dates). Overlap NAV levels are **not** a pure dividend A/B — challenger started earlier. Use §4a for economics; use §4b for “official loop + QC + dividends fire”.

---

## 5. Promotion path checklist

| Step | Status |
|---|---|
| FROZEN_BASELINE preserved | **PASS** — E21 untouched |
| CHALLENGER separate folder | **PASS** |
| Named hypothesis | **PASS** |
| Side-by-side report | **PASS** (this file) |
| OOS / cost | **PASS** — fees/tax/slippage unchanged vs E21; dividend is cash credit not a cost change |
| Stress / MC | **INCONCLUSIVE_LIGHT** — MDD not worsened on full-history book; no separate MC required for cash accounting fix |
| Governance review | **PASS** — human approval 2026-09-04 |
| Explicit approval | **PASS** — phrase matched |
| NEW FROZEN VERSION recorded | **PASS** — `E22_v2_CASH_EX_OFFICIAL_PATH` |

Research decision (engineering): **`PASS_RECOMMEND_PROMOTE`**  
Governance decision: **`APPROVED`** (2026-09-04)

Implemented:

- `scripts/e22_v2_forward_pipeline.py` / `scripts/e22_v2_qc.py`
- `forward/e22_v2/` cutover seed from E21 (no dividend backfill)
- `research/e22/E22_v2_STATUS.md`
- Additive updates to `FROZEN_GOVERNANCE.md` / `FROZEN_STRATEGY_SPEC.md`
- `forward/e21/` preserved untouched

---

## 6. What approval means (implementation recipe)

~~Only after explicit approval:~~ **DONE 2026-09-04**

1. Publish additive docs: `research/e22/E22_v2_STATUS.md` — **done**  
2. New versioned script/path — **done** (`e22_v2_forward_pipeline.py`)  
3. Fresh forward state dir from cutover — **done** (`forward/e22_v2/`)  
4. Update frozen docs additively — **done**

---

## 7. Explicit non-actions (still in force)

- Do not edit `scripts/e21_forward_pipeline.py` in place  
- Do not append dividend backfills into past `forward/e21/nav.csv`  
- Do not edit `e22_v2` in place for further dividend-rule changes (new challenger required)

---

## 8. Sign-off

| Role | Decision | Date | Name |
|---|---|---|---|
| Research (this PR) | Recommend **PASS → promote as new version** | 2026-09-04 | Cursor agent |
| Governance / human | **APPROVED** | 2026-09-04 | User (approval phrase) |

**Approval phrase (received):**  
`APPROVE E22_v2_CASH_EX_OFFICIAL_PATH — wire cash_ex_date credits into official exec path as new SOFT_FROZEN version; preserve forward/e21 forever.`
