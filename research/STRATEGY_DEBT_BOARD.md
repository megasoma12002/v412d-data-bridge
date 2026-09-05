# Strategy Debt Board

Date: 2026-09-05 (code-review residual clear: e21_qc Exact T+1)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Glossary (do not collapse)

| Term | Meaning |
|---|---|
| **SOFT_FROZEN** (class) | Official strategy-version class for E16/E18/E22/E45 — **not** “is live” |
| **Live Soft-Frozen clip** | Live E16 Financial band **[0.50, 0.95]** |
| **Dual-paper** | Parallel Exact T+1 paper books — observation only |
| **Cutover** | Human PR that changes live books / live clip / live path logic |

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| L1/L2/L3 MDD engines | All MIXED stop on sealed CAGR |
| FIN_CAP_50 go-live verify | Artifact on main — **`NOT_READY_SEALED_CAGR`** (sealed gb +4.33; PAUSE 1y/YTD) |
| Sealed CAGR improve diagnostics | CRISIS_ONLY / FIN70 / BLEND sealed-diag survivors |
| L4 path/mild-FIN charter | Frozen — util-rank; no harsh-cap family priority |
| L4 Exact T+1 OOF → adv-lite → held-out | **`PASS_HELDOUT_L4`** — on main via #51 |
| Dual-track A/B | On main via #37 — A KEEP / B S1 STOP |
| Code-review fixes (round 1) | Month-end `0→nan`; fin_cap single-source; Soft-Frozen vs live wording |
| Code-review P2 | Soft-Frozen BASE single-source (`e16_soft_frozen_base`); live Exact T+1 `qc_status.json`; scorers drop `x or 0`/`mdd or 9` |
| Code-review residual | `e21_qc` defaults to `forward/e21` + preserves Exact T+1; SPEC live banner; FIN_CAP OOF None-safe deltas |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Paper/monitor harness + month-end KPI | **KEEP** |
| Live Soft-Frozen clip | **[0.50, 0.95]** | **KEEP (no auto flip)** |
| FIN_CAP_50 paper | Dual-paper observation | **OPERATING (paper)** |
| FIN_CAP_50 cutover | Blocked by go-live | **`NOT_READY_SEALED_CAGR` / FROZEN** |
| L4 dual-paper | BASE vs `L4_DD_PATH_08_50` paper books + month-end | **OPERATING (paper)** |
| L4 cutover | Human PR only after clean month-end | **FROZEN (not Soft-Frozen flip)** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| L4 month-end | ≥1 review via `e16_l4_dd_path_month_end_monitor.py` | Treat dual-paper as Soft-Frozen flip |
| L4 cutover PR (later) | Wire **DD-path logic** only after clean month-end + explicit approval | Static clip swap; auto live-wire |
| FIN_CAP month-end | Continue; alerts now include YTD/1y (Gate E) | Auto-promote FIN50 / ignore `NOT_READY` |
| Track A month-end | Refresh KPI via `scripts/e50a_dual_track_s9a1_monitor.py` | Retune S9A1 cuts |
| New alpha charter | Only with a **new** charter (not S1 residual re-grid) | Reopen S1 / TECH2 remix |

### WON’T
L1/L2/L3/FIN50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 / L4 without human PR; reopen S1 residual detector grid; conflate FIN50 static promote with L4 DD-path cutover.

## Cutover matrix (human PR only)

| Challenger | Live change type | Blocked by | Soft-Frozen clip today |
|---|---|---|---|
| FIN_CAP_50 | Static Financial clip → **[0.35, 0.50]** | `NOT_READY_SEALED_CAGR` + YTD/1y PAUSE | **[0.50, 0.95]** |
| L4_DD_PATH_08_50 | Wire **path-dependent DD-path** logic (not static clip) | Need ≥1 clean month-end + human PR | **[0.50, 0.95]** |
| E50-A / E45 | Overlay / crisis attach | Not live-wired; E45 NOT_VERIFIED | N/A (core-only live) |

## Snapshot
| Topic | Number |
|---|---|
| Go-live (FIN50) | **`NOT_READY_SEALED_CAGR`** |
| FIN50 dual-paper | **OPERATING** / cutover **FROZEN** |
| L4 held-out | **`PASS_HELDOUT_L4`** (`L4_DD_PATH_08_50`) |
| L4 dual-paper | **OPERATING** / cutover **FROZEN** |
| Track A | **KEEP** (S9A1 paper/monitor) |
| Track B S1 | **`STOP_S1_HELDOUT_KEEP_TRACK_A`** |
| Soft-Frozen clip | **[0.50, 0.95]** |

## Pointers
- `scripts/e16_soft_frozen_base.py` (live Financial clip **[0.50, 0.95]**)
- `scripts/e21_forward_pipeline.py` / `scripts/e21_qc.py` (canonical `forward/e21`; Exact T+1 in `qc_status.json`)
- `scripts/research_metric_helpers.py`
- `research/gaps/L4_DD_PATH_PROMOTE_PROPOSAL.md`
- `research/gaps/L4_DD_PATH_MONTH_END_RUNBOOK.md`
- `research/gaps/MDD_L4_HELDOUT.md`
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
- `research/gaps/FIN_CAP_50_PROMOTE_PROPOSAL.md` (cutover blocked banner)
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`
