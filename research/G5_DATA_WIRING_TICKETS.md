# G5 Data / Wiring Tickets

Date: 2026-09-04  
Scope: remaining HARD_FROZEN honesty + official-path wiring after P0/P1  
Status: **ticketed** — not executed as in-place frozen rebuilds

Companion: `research/GAP_FILL_PLAN.md` §5

---

## T1 — E22 → official path (scheduled)

| Field | Value |
|---|---|
| Status | **PROMOTED** → `E22_v2_CASH_EX_OFFICIAL_PATH` |
| Artifact | Official: `forward/e22_v2/` + `scripts/e22_v2_forward_pipeline.py` |
| Evidence | Full-history CAGR +3.97 pp; paper challenger QC PASS; human approval 2026-09-04 |
| Promotion package | `research/e22/E22_PROMOTION_PACKAGE.md` (**APPROVED**) |
| Status doc | `research/e22/E22_v2_STATUS.md` |
| Next | Run daily `e22_v2_forward_pipeline.py`; keep `forward/e21/` forever |
| Forbidden | Editing `e21_forward_pipeline.py` or rewriting `forward/e21/` history; in-place v2 retunes |

---

## T2 — A1 `available_date` / causal residuals

| Field | Value |
|---|---|
| Status | **DOCUMENTED_LIMITATION** |
| Issue | Causal contract is HARD_FROZEN; any `available_date` vs statutory/effective residuals need a **data challenger rebuild** with QC delta — not a silent patch |
| Source | `research/e50a1/README.md` knowledge-date contract |
| Next | Open only if a reproducible QC FAIL is found against pinned A1 hashes |
| Forbidden | Rebuild A0/A1/A2 without defect (`START_CURSOR.md`); overwrite prior baseline in place |

---

## T3 — A0 industry master snapshot

| Field | Value |
|---|---|
| Status | **DOCUMENTED_LIMITATION** |
| Issue | FinMind stock master is a **current** industry snapshot, not historical reclassification |
| Source | `research/e50a0/README.md` §Known boundary |
| Impact | Industry-neutral alpha scores remain unsafe on A0 alone; belongs to future A1+ historical industry PIT |
| Next | Acquire historical industry PIT source **or** keep limitation explicit in alpha docs |
| Forbidden | Pretending current master is PIT industry history |

---

## T4 — E16 full-history API surface

| Field | Value |
|---|---|
| Status | **DONE_THIN_API** (this PR) |
| Artifact | `scripts/e16_core_api.py` — wraps E21 constants + `e16_features` / `simulate_core` without editing E21 |
| Note | Reconstruction already lives in `e50_early_stack_combined_nav.py`; API is an importable name for G2 consumers |
| Forbidden | Claiming this promotes a new E16 frozen version |

---

## T5 — E22 early-year `cash_payment_date` backfill

| Field | Value |
|---|---|
| Status | **PARTIALLY_CLOSED_FREE_SOURCES** |
| Issue | 29 cash events (mostly 2010–2014) lack `CashDividendPaymentDate` in FinMind |
| Attempt | MOPS `t108sb27` reconcile (`scripts/e22_reconcile_payment_dates_mops.py`) — same blanks; **0** official fills |
| Artifacts | `e22_payment_date_gap_report.json`; research proxy `e22_payment_date_research_proxy.csv` (median lag 28d, **not** merged into official ledger) |
| Source map | `research/DATA_GAP_SOURCE_MAP.md` |
| Next | Manual IR/年報 or paid CA vendor for true dates before fair E22_v3 H1 |
| Forbidden | Merging `PROXY_MEDIAN_LAG` into official `e22_dividend_events.csv` / `e22_v2` |

---

## Priority

```
T1 done  >  T5 (vendor/manual payment dates for E22_v3)  >  T3 (industry PIT if alpha reopens)  >  T2 (only on QC defect)
T4 done
```

No ticket here authorizes gate promotion or more same-panel alpha grids (see `GOVERNANCE_ALPHA_PANEL_SATURATED.md`).

See also: `research/DATA_GAP_SOURCE_MAP.md` for challenger fetch locations (industry PIT, lending, futures OI, G4 instruments).
