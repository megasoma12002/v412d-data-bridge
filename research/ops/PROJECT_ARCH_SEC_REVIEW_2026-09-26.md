# Project Architecture & Security Code Review — 2026-09-26

Scope: full-repo system architecture + security trust-boundary review on `main`  
(post Class D FinPriv V7 F05 live wire · COOL_c8 · β densify · Gate V7/V8 paper).  
Priors: `PROJECT_CODE_REVIEW_2026-09-12.md` · `ARCH_LIVE_MODULARIZE.md` · `OPS_STATUS.md`

Label: `PROJECT_ARCH_SEC_REVIEW_2026-09-26__REMEDIATED`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| System layering (data → paper → live tip → ops/CI) | **HEALTHY** | Clear Soft-Frozen tip vs paper coexistence |
| Live day modular pipeline | **HEALTHY** | Thin CLI + `live_*` modules; session lock |
| Soft-Frozen SSOT / ACCEPT gates | **HEALTHY** | `live_config` + ballots + checklists |
| Exact T+1 / QC / tip-write chain | **HEALTHY** | Fail-closed; tip gate asserts QC + Exact T+1 |
| Broker live-write | **PREP / FAIL-CLOSED** | Triple gate + `API_WIRED=False` |
| Class D FinPriv carve | **WIRED · ALERTED** | Fail-closed stale px + ops HIGH alert + CI tip refresh |
| CI tip-writer blast radius | **ACCEPTABLE · HIGH CARE** | Owner-only issues; `contents: write` |
| Docs vs live SSOT lag | **REMEDIATED** | KEEP/ARCHIVE + register banner synced to FUSE+COOL+Class D |
| Overall security posture | **STRONG for paper tip** | Residual INFO only (broker PREP, tip blast radius care) |

---

## Residual remediations (this follow-up)

| ID | Was | Fix |
|---|---|---|
| S1 | Tip-write gate skipped QC | `forward_tip_write_gate.py` requires `qc_status` PASS + `exact_t1_ok` |
| S2 | Class D stale px silent | `ops_alert_scan` HIGH `FINPRIV_PX_STALE_OR_MISSING` / tip skip; CI `private_fin_adj_tip_refresh.py` on E22 weekday job |
| S4 | FINMIND_TOKEN job-wide on E22 | Step-scoped env on dividend + priv tip steps |
| S6 | Cash-clock confusion | Tip-gate docstring cites three cash views (never merge) |
| S7 | KEEP/ARCHIVE / register still said DH live | Synced to FUSE+COOL+Class D |

Deferred (INFO / ops care only): S3 tip-writer `contents: write` blast radius (concurrency + owner gate KEPT); S5 hygiene `exec` on trusted harness; S8 broker PREP keep.

---

## Architecture one-liner

**Data builds Soft-Frozen tip market → modular live day (3-sleeve + FUSE/COOL + Class D carve + Stage-E books) commits immutable `forward/e21` under lock → QC + post-forward + tip-write gate (QC+books) → bot push; paper dual-ledgers share SSOT without flipping live.**
