# G5 Data / Wiring Tickets

Date: 2026-09-04  
Scope: remaining HARD_FROZEN honesty + official-path wiring after P0/P1  
Status: **ticketed** — not executed as in-place frozen rebuilds

Companion: `research/GAP_FILL_PLAN.md` §5

---

## T1 — E22 → official path (scheduled)

| Field | Value |
|---|---|
| Status | **PAPER_READY** |
| Artifact | `forward/e22_challenger/` + `scripts/e22_challenger_forward_pipeline.py` |
| Evidence | Full-history E16 book CAGR +3.97 pp; live 9-session paper QC PASS (no ex-date in window) |
| Next | Keep paper-parallel with E21 → explicit approval → **new** SOFT_FROZEN E22 version |
| Blocked by | Governance approval (not engineering) |
| Forbidden | Editing `e21_forward_pipeline.py` or rewriting `forward/e21/` history |

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

## Priority

```
T1 (governance)  >  T3 (if new-info alpha reopens)  >  T2 (only on QC defect)
T4 done
```

No ticket here authorizes gate promotion or more same-panel alpha grids (see `GOVERNANCE_ALPHA_PANEL_SATURATED.md`).
