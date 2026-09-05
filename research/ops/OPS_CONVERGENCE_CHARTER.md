# Ops Convergence Charter — Research Only

Date: 2026-09-05  
Label: `OPS_CONVERGENCE_RESEARCH`  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP** — this charter never flips it.  
Live wire / auto-cutover: **FORBIDDEN**.

## 0. Problem

The repo already has:

- a **daily live forward** path (`e21_build_market` → `e21_forward_pipeline` → `e21_qc`)
- **paper challengers** (FIN_CAP_50, L4_DD_PATH_08_50, Track A S9A1) with month-end monitors

What it does **not** yet have is a single **operable system**: one entry map, one cadence, live↔paper reconciliation, and fail-closed ops gates that do not depend on human memory.

Goal of this charter: design and stage that convergence **without** promoting any challenger to live.

## 1. Non-goals (WON’T)

- Soft-Frozen clip edit / auto flip
- FIN50 or L4 cutover / live-wire
- E45 / E50-A overlay attach
- Retune Stage-8 / S1 / locked FIN50 / L1–L3
- Rewrite `forward/e21` history
- Treat dual-paper PASS / held-out PASS as cutover license

## 2. Target operating picture

```
                    ┌─────────────────────────────┐
  Daily (weekday)   │ LIVE CORE (Soft-Frozen)     │
  GHA already runs  │ E16 + Exact T+1 E18 + E22   │
                    │ forward/e21 + qc_status     │
                    └──────────────┬──────────────┘
                                   │ recon (research)
                                   ▼
                    ┌─────────────────────────────┐
  Month-end         │ PAPER SLEEVES (observe)     │
  (to automate)     │ FIN50 │ L4 │ Track A S9A1   │
                    │ alerts → debt board only    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
  Human only        │ CUTOVER PR (later, gated)   │
                    │ never from this charter     │
                    └─────────────────────────────┘
```

## 3. Current inventory (asof 2026-09-05)

### Live (operable daily)

| Piece | Path |
|---|---|
| Workflow | `.github/workflows/v412f-forward-paper.yml` (cron `30 8 * * 1-5`) |
| Market | `scripts/e21_build_market.py` → `forward/e21/live_market.csv` |
| Pipeline | `scripts/e21_forward_pipeline.py` → nav/orders/fills/signals |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` (Exact T+1 preserved) |
| Clip source | `scripts/e16_soft_frozen_base.py` **[0.50, 0.95]** |

### Paper (scripted, manual cadence)

| Sleeve | Ledgers | Month-end | Runbook |
|---|---|---|---|
| L4 | `scripts/e16_l4_dd_path_dual_paper_ledgers.py` | `..._month_end_monitor.py` | `research/gaps/L4_DD_PATH_MONTH_END_RUNBOOK.md` |
| FIN50 | `scripts/e16_fincap50_dual_paper_ledgers.py` | `..._month_end_monitor.py` | `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md` |
| Track A | `scripts/e50a_dual_track_s9a1_monitor.py` | archive bootstrap | dual-track board / S9A1 runbook |

### Authority docs (sprawl risk)

| Doc | Role |
|---|---|
| `research/STRATEGY_DEBT_BOARD.md` | **Ops truth** — Now/Next/cutover matrix |
| `HANDOFF.md` | Onboarding read order |
| `FROZEN_GOVERNANCE.md` / `FROZEN_STRATEGY_SPEC.md` | Class & roles — **not** live wiring proof |
| `README.md` | Historically research-start only (updated by this charter to point at ops map) |

## 4. Gap list (severity)

| ID | Severity | Gap | Desired state |
|---|---|---|---|
| G1 | **P0** | No live↔paper Soft-Frozen recon | Daily/on-demand script + artifact under `research/ops/` |
| G2 | **P0** | Month-end monitors not on calendar/CI | Scheduled workflow **or** checklist bot; fail = open issue, never cutover |
| G3 | **P0** | No single ops entry map | `research/ops/OPS_STATUS.md` + README pointer |
| G4 | **P1** | No PR/smoke path for live QC only | Lightweight job: qc on existing `forward/e21` without full data rebuild |
| G5 | **P1** | Track A runbook not co-located with L4/FIN50 | Pointer from `research/ops/` + gaps index |
| G6 | **P1** | Shadow sleeves (E6/E9/E10) inflate “what is live?” | Ops status labels them SHADOW |
| G7 | **P1** | Dual mirrors (`repro/` + `research/gaps/`) can drift | Canonical = `research/gaps/*_MONTH_END_MONITOR.*`; repro = raw |
| G8 | **P1** | MTD annualized CAGR misleads | Monitors mark MTD as non-decision (display only) |
| G9 | **P2** | No alert routing on QC FAIL / PAUSE_REVIEW | Issue label or workflow summary annotation |
| G10 | **P2** | Artifact retention policy undocumented | Document GHA 90d + git-tracked monitors |
| G11 | **P2** | `forward/config.json` legacy vs E21 live | Annotate or freeze-as-legacy |

## 5. Phased plan (research → ops glue only)

### Phase 0 — Map & recon (this PR)

- [x] Charter (`OPS_CONVERGENCE_CHARTER.md`)
- [x] One-page status (`OPS_STATUS.md`)
- [x] README → ops entry
- [x] `scripts/e21_live_vs_paper_recon.py` (Soft-Frozen live vs dual-paper BASE overlap)
- [x] Debt board NEXT points here

**Exit:** ops map readable in ≤2 minutes; recon artifact exists. First overlap shows thin live history (~10 sessions) and mild indexed drift — expected, not a cutover signal.

### Phase 1 — Cadence without cutover

- [x] Month-end workflow (`ops-month-end-paper-pack.yml`, `workflow_dispatch` + monthly cron) via `scripts/ops_month_end_paper_pack.py`
  1. L4 month-end monitor (optional ledger refresh)  
  2. FIN50 month-end monitor (optional ledger refresh)  
  3. Track A monitor bootstrap  
  4. Live↔paper recon + `research/ops/MONTH_END_PAPER_PACK.*` — **never** edits Soft-Frozen
- [x] Live QC smoke workflow (`e21-live-qc-smoke.yml`, qc-only on `forward/e21`)

**Exit:** one button / schedule produces all three paper monitors + recon. Soft-Frozen unchanged. No auto cutover.

### Phase 2 — Ops hygiene

- [x] Mark MTD CAGR non-decision in L4 / FIN50 month-end monitors  
- [x] Track A runbook pointer under `research/ops/` (`TRACK_A_RUNBOOK_POINTER.md`)  
- [x] Artifact retention + canonical paths (`ARTIFACT_RETENTION.md`)  
- [x] Shadow sleeves labeled in OPS_STATUS  
- [x] Gated cutover checklists (prep only): `CUTOVER_CHECKLIST_L4.md`, `CUTOVER_CHECKLIST_FIN50.md`

**Exit:** new agent can operate month-end without reading SPEC as live; cutover remains checklist-blocked.

### Phase 3 — Explicitly out of scope here

- L4 / FIN50 cutover human PRs (remain on debt-board gates)
- New alpha / sealed-CAGR research charters (separate)

## 6. Acceptance gates (for calling the system “operable”)

A system is **ops-ready** when all hold:

1. Soft-Frozen live clip still **[0.50, 0.95]** and single-sourced  
2. Weekday live job green **or** FAIL blocks with Exact T+1 visible in `qc_status.json`  
3. Live↔paper recon runs and explains any NAV/weight drift on overlap dates  
4. L4 + FIN50 + Track A month-end can be produced by a documented single command/workflow  
5. Debt board is the only cutover authority; OPS_STATUS never claims READY for frozen cutovers  
6. README lands a newcomer on OPS_STATUS in one click  

## 7. First recon note (Phase 0)

Live `forward/e21/nav.csv` currently spans **~10 sessions** (from 2026-08-24).  
Dual-paper BASE spans **2012-12-04 → asof**.  

Overlap recon therefore starts **thin by construction**. That is expected: operable ≠ long live history. Do not invent live CAGR from a 10-day window.

## 8. Decision label

`OPS_CONVERGENCE_CHARTER_OPEN__NO_LIVE_CHANGE`

Next implementer: execute Phase 1 workflow draft under a **new** PR; keep Soft-Frozen untouched.
