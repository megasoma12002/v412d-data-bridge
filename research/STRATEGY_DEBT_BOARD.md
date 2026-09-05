# Strategy Debt Board

Date: 2026-09-05 (strategy closure prep — claim policy + BLEND checklist)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).  
Human decisions: `research/ops/HUMAN_DECISION_REGISTER.md`  
Live claims: `research/ops/LIVE_CLAIM_TARGET_POLICY.md`

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
| Code-review residual path | Through #56 |
| Ops Phase 0 | Map + recon (#58) |
| Ops Phase 1 | Live QC smoke + month-end pack (#59) |
| Ops Phase 2 hygiene | MTD non-decision; retention; Track A pointer; cutover checklists — **#60** |
| Ops hardening | Alert scan + GHA summaries; E22 data-quality KPI in pack; five-layer checklist; forward legacy note — **#61** |
| Layer-3 Gap #6 fidelity | Ex→pay / receivable / tax / live evidence KPI + odd-lot promote checklist — **#62** |
| FIN50 sealed-CAGR improve charter | `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md` (research path; Soft-Frozen KEEP) |
| FIN50 charter screen → BLEND_025 | Screen PASS → paper-promote proposal only (#64) |
| BLEND_025 dual-paper observe | Ledgers + month-end + pack/alert wire — **OPERATING OBSERVE** (#65) |
| Human decision register | Soft-Frozen KEEP; FIN50 static REJECT; BLEND observe; L4/BLEND live DEFER — `HUMAN_DECISION_REGISTER.md` |
| BLEND_025 cutover checklist (prep) | `CUTOVER_CHECKLIST_BLEND025.md` — **NOT AUTHORIZED** |
| Live claim / target policy | `LIVE_CLAIM_TARGET_POLICY.md` — live may not claim CAGR/MDD badges |
| Post-forward E22 verify runbook | `POST_FORWARD_E22_VERIFY_RUNBOOK.md` — weekday ops prep |
| Obs PR #57 | **Superseded** by #58/#59 cadence (leave closed/ignored if API cannot close) |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Paper/monitor via month-end pack | **KEEP** |
| Live Soft-Frozen clip | **[0.50, 0.95]** | **KEEP** (register #1) |
| FIN_CAP_50 paper | Dual-paper + pack | **OPERATING**; **static cutover REJECT for now** (register #2) |
| L4 dual-paper | Dual-paper + pack | **OPERATING**; cutover **DEFER** until clean month-end (register #4) |
| BLEND_025 dual-paper | Dual-paper + pack + runbook | **OPERATING OBSERVE** — sole sealed-CAGR successor (register #3); live **NOT READY** (#5) |
| Cutover checklists | `CUTOVER_CHECKLIST_{L4,FIN50,BLEND025}.md` | L4/FIN50 **BLOCKED**; BLEND025 **PREP / NOT AUTHORIZED** |
| Live claim policy | `LIVE_CLAIM_TARGET_POLICY.md` | **BINDING** — no live target badges |
| Human decision register | `research/ops/HUMAN_DECISION_REGISTER.md` | **BINDING** 2026-09-05 |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Strategy update SOP | Use `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md` for any future challenger / Soft-Frozen / live-path change | Skip classify→observe→register→checklist→human PR |
| Calendar month-end | Re-run pack; watch L4/FIN50/BLEND_025 trailing | Treat pack green / observe clean as cutover |
| Live↔paper recon | Re-check INDEX_DRIFT as live history lengthens | Decision on <60 live sessions |
| Live E22 field evidence | After next weekday forward; run `POST_FORWARD_E22_VERIFY_RUNBOOK.md` | Rewrite `forward/e21` history |
| L4 cutover PR | Only after register re-open trigger + checklist all-green | Soft-Frozen flip; static clip swap; open PR while PAUSE |
| FIN50 static cutover PR | **Do not open** while `NOT_READY_SEALED_CAGR` | Retune FIN50 lock; ignore `NOT_READY` |
| BLEND_025 live-wire | Only after `CUTOVER_CHECKLIST_BLEND025` all-green + human PR | Treat observe PASS / checklist draft as promote |
| E45 / odd-lot / tax books | Item3 stitch **DEFERRED**; paper feasibility **`FEASIBLE_CONTINUE_PAPER`** (not live-ready); see `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.md` | Four-layer live stitch; silent default promote; treat −13.16% as verified; open live ballot before cost/stress seal |

### WON’T
L1/L2/L3/FIN50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 / L4 / BLEND_025 without human PR; reopen S1 residual detector grid; conflate FIN50 static promote with L4 DD-path or BLEND_025 observe.

## Cutover matrix (human PR only)

| Challenger | Live change type | Blocked by | Soft-Frozen today | Checklist |
|---|---|---|---|---|
| FIN_CAP_50 | Static clip → **[0.35, 0.50]** | `NOT_READY_SEALED_CAGR` + YTD/1y PAUSE | **[0.50, 0.95]** | `CUTOVER_CHECKLIST_FIN50.md` |
| L4_DD_PATH_08_50 | Wire DD-path logic | YTD PAUSE + need clean month-end + human PR | **[0.50, 0.95]** | `CUTOVER_CHECKLIST_L4.md` |
| BLEND_025 | Soft-Frozen → blend weights | Observe ≠ promote; checklist prep only | **[0.50, 0.95]** | `CUTOVER_CHECKLIST_BLEND025.md` (**NOT AUTHORIZED**) |
| E50-A / E45 | Overlay / crisis | E45 Soft-Frozen CRITICAL; artifact NOT_VERIFIED; stitch DEFERRED; live auth NO; paper `FEASIBLE_CONTINUE_PAPER` | N/A | `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.md` |

## Snapshot
| Topic | Number |
|---|---|
| Go-live (FIN50) | **`NOT_READY_SEALED_CAGR`** |
| FIN50 / L4 dual-paper | **OPERATING** / cutover **FROZEN** |
| BLEND_025 dual-paper | **OPERATING OBSERVE** / cutover **blocked** |
| L4 held-out | **`PASS_HELDOUT_L4`** |
| Track A | **KEEP** |
| Soft-Frozen clip | **[0.50, 0.95] KEEP** (register #1) |
| Human decisions | `research/ops/HUMAN_DECISION_REGISTER.md` **BINDING** |

## Pointers
- `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`
- `research/ops/HUMAN_DECISION_REGISTER.md`
- `research/ops/LIVE_CLAIM_TARGET_POLICY.md`
- `research/ops/CUTOVER_CHECKLIST_BLEND025.md`
- `research/ops/POST_FORWARD_E22_VERIFY_RUNBOOK.md`
- `research/ops/FIVE_LAYER_GAP_CHECKLIST.md`
- `research/ops/OPS_STATUS.md`
- `research/ops/OPS_ALERTS.md`
- `research/ops/E22_DATA_QUALITY_KPI.md`
- `research/ops/E22_GAP6_FIDELITY_KPI.md`
- `research/gaps/BLEND_025_DUAL_PAPER_OBSERVE.md`
- `research/gaps/BLEND_025_MONTH_END_RUNBOOK.md`
- `research/gaps/FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md`
- `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`
- `research/ops/ARCHIVE_SENTINEL_HYGIENE.md`
- `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`
- `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`
- `research/ops/LIVE_E22_FIELD_EVIDENCE.md`
- `research/ops/FORWARD_LEGACY_NOTE.md`
- `scripts/ops_alert_scan.py`
- `scripts/e22_data_quality_kpi.py`
- `scripts/e22_gap6_fidelity_kpi.py`
- `research/ops/OPS_CONVERGENCE_CHARTER.md`
- `research/ops/ARTIFACT_RETENTION.md`
- `research/ops/CUTOVER_CHECKLIST_L4.md`
- `research/ops/CUTOVER_CHECKLIST_FIN50.md`
- `research/ops/TRACK_A_RUNBOOK_POINTER.md`
- `research/ops/MONTH_END_PAPER_PACK.md` / `LIVE_PAPER_RECON.md`
- `.github/workflows/e21-live-qc-smoke.yml`
- `.github/workflows/ops-month-end-paper-pack.yml`
- `scripts/ops_month_end_paper_pack.py`
- `scripts/e16_soft_frozen_base.py`
- `scripts/e21_qc.py` / `e21_live_vs_paper_recon.py`
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`
