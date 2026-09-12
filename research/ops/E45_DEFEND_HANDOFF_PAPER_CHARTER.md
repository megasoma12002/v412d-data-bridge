# E45 Defend-Window → Handoff Paper Charter (one page)

Date: 2026-09-12  
Status: **PAPER CHARTER OPEN** · Stage A screen **NOT RUN**  
Soft-Frozen **KEEP** · live stack **KEEP** · E45 live stitch **FORBIDDEN** (do **not** reopen)  
DEFAULT / Soft-assist / Sleeve-tilt / FUSE_ADDITIVE observes **unchanged**

Ballot label: `E45_DEFEND_HANDOFF_PAPER_CHARTER_2026-09-12__PAPER_OPEN__NO_STITCH`

## Why

E45-class overlays improve MDD but burn CAGR in calm / rebound windows (hence `DROP_E45_A05`).  
Ask: can a **finite paper** book (1) enter defense only on a hard trigger, (2) **exit** on a hard exit rule, (3) **hand capital back** to a named offense book — without live stitch?

This is **not** another mild-α / crisis-gate / max_cut densify of frozen E45 knobs (those are exhausted). It is a **new role**: temporary defense window + explicit handoff.

## Three clauses (SSOT)

### 1) Trigger（觸發）

Enter defense iff **all** hold (Exact T+1, no peek):

| ID | Rule (Stage A freeze) |
|---|---|
| `T1` | Sleeve or book NAV drawdown from peak ≥ **8%** within **63** trading days |
| `T2` | Broad risk-off confirm: FIN sleeve 21d realized vol z ≥ **+1.5** **or** 0050 63d MDD ≤ **−10%** |
| `T3` | Min dwell before re-check: **5** sessions after prior exit (anti-churn) |

Stage A may test the finite grid `{dd: 6/8/10%} × {vol_z: 1.0/1.5}` — **no open search**.

### 2) Exit（出場）

Leave defense on **first** of:

| ID | Rule |
|---|---|
| `X1` | NAV recovered to ≥ **97%** of pre-trigger peak |
| `X2` | **42** sessions in defense with no new `T1` breach |
| `X3` | Defense sleeve trailing 21d return > offense sleeve by **>0** (handoff race lost → force exit) |

No discretionary override in the screen.

### 3) Handoff book（接手書）

| Phase | Book | Notes |
|---|---|---|
| Offense (default) | `LIVE_STACK` | Soft-Frozen + KD_OPT + TEL_EQUAL — **paper twin**, not live wire |
| Defense (active window) | `E45_DEFEND_WIN` | Sleeve-local or cash/defensive relocate actuator (reuse M2-style relocate **paper** only; freeze one recipe in screen script) |
| Optional paper challengers (report-only) | Soft observe / Sleeve observe / `FUSE_ADDITIVE` | **Receive handoff in alternate rows only**; never auto-promote |

Handoff = full weight return to offense book on exit; no residual E45 blend after `X*`.

## Stage A question

Does any finite trigger×exit×defend recipe **promote-shaped-beat** `LIVE_STACK` on held-out score **and** tip YTD/1y MDD not worse than base, **with** CAGR giveback ≤ **2.0 pp** on held-out?

| Verdict | Meaning |
|---|---|
| `HANDOFF_PROMOTE_SHAPED` | Clears tip hygiene + held score>0 + giveback≤2pp |
| `MDD_HELP_CAGR_FAIL` | MDD↑ but giveback fails (expected baseline risk) |
| `NO_LIFT` | No recipe clears |

Even `HANDOFF_PROMOTE_SHAPED` → **paper observe ballot only**; **never** live stitch from this charter.

## Explicit non-actions

- **No E45 live stitch reopen** · no undo of `DROP_E45_A05`  
- No Soft-Frozen / KD / TEL / Soft-assist / Sleeve / FUSE live wire  
- No inventing replacement for `RETIRED_HISTORICAL_NARRATIVE` MDD  
- No same-knob E45 densify (mild α / crisis-gate / mild max_cut) as the mechanism  
- No ops Soft∥Sleeve auto-fuse  

## Artifacts (on go)

- Screen script (to implement): `scripts/e45_defend_handoff_stagea_screen.py`  
- Reports: `research/ops/E45_DEFEND_HANDOFF_STAGEA_SCREEN.md` · `repro/e45-defend-handoff-stagea/`  
- ZH: `E45_DEFEND_HANDOFF_PAPER_CHARTER.zh-TW.md`

## Next authorized action

Human says go → run **Stage A paper screen only** → stop for Architect review.  
**Not** authorized: observe OPEN, cutover, or stitch ballot.
