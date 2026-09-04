# Gap-Fill Research Plan — What Is Missing and How to Close It

Date: 2026-09-04  
Scope: early stack (E16/E18/E22/E45) + E50-A overlay + four-layer engine  
Status: **research plan only** — does not promote SOFT_FROZEN versions

Companion evidence already in repo:

- `research/e45/E45_MODULE_STATUS.md`
- `repro/early-stack-combined-nav-20260904/` (core + named E45 + four-layer mix)
- `FROZEN_GOVERNANCE.md`, `FROZEN_STRATEGY_SPEC.md`
- A3-R1 / Option-2 archive (alpha MIXED; panel saturated)

---

## 0. Gap map (priority order)

| # | Gap | Why it matters | Current state |
|---|---|---|---|
| G1 | **Official E45 crisis core** | Spec says crisis protection is E45; without promotion there is no locked hedge engine | Named module exists; `CHALLENGER_CANDIDATE_NOT_PROMOTED`; MDD −13.16% UNVERIFIED |
| G2 | **Production four-layer live engine** | Roles ≠ daily order state machine | Challenger NAV books only; E21 live is core-short ledger |
| G3 | **Promotable alpha** | Overlay must earn its sleeve or stay paper | A3-R1 / S9A1 MIXED; same-panel search saturated |
| G4 | **True hedge instruments** (optional product choice) | “Crash also profit” needs more than de-lever | Only exposure cut / sleeve tilt / alpha-cut-first |
| G5 | **Data / wiring debts** | Causality + economics of official path | E22 not in E21 fills; A1 CA residuals; A0 industry snapshot |

**Do not** try to close G3 by retuning TECH2 grids, or G1 by editing E45 in place.

---

## 1. G1 — How to complete official E45

### Goal
A **promoted** crisis core with:

- importable baseline module (already: `scripts/e45_crisis_core.py`)
- **verified** performance artifact (replace or retire −13.16% claim)
- side-by-side vs preserved **V4.12-D** (formal strategy today)
- higher bar than E16/E18/E22 challengers

### Method (ordered)

1. **Freeze the claim ledger**  
   - Keep `CLAIMED_MDD = -13.16%` as `UNVERIFIED_TEXT_ONLY`.  
   - Publish `VERIFIED_BASELINE_MDD` from a reproducible run (D and/or E3 on the same raw/adj panels used in `v412e2_e3_three_rounds.py`).  
   - Output: `research/e45/e45_verified_baseline.json` (NAV path hashes, window metrics).

2. **E45-C1 challenger folder** (new, do not overwrite lineage)  
   - Candidates (small set, no mega-grid):  
     - `PASSTHROUGH` (control)  
     - `E1_BINARY` (locked defaults)  
     - `E3_VOLTARGET_WINNER` (locked from `e3_status.json`)  
     - at most **one** new schedule (e.g. slower recovery) marked EXPERIMENTAL  
   - Host book: prefer **V4.12-D formal router** for apples-to-apples; second track = E16 core-only book (document adaptation).

3. **Higher validation bar** (process, not new magic numbers unless approved)  
   - Crisis windows: 2008–09, plus any pre-registered list  
   - Block-bootstrap / MC on **drawdown protection** vs preserved D  
   - Cost sensitivity (already patterned in E3)  
   - Must not weaken HARD_FROZEN clock / PIT  
   - **No retune after opening Blind/Final**

4. **Promotion decision options**  
   - **A.** Promote E3-locked profile as `E45_v1` with verified MDD artifact; retire −13.16% text.  
   - **B.** Keep D as crisis baseline; E45 module stays “API + documentation of D’s risk layer” only.  
   - **C.** Reject all; leave candidate unpromoted (status quo with honesty).

### Stop rules
- If no candidate beats D on the higher bar → **do not invent** a friendlier gate.  
- If only E16-adapted universe “wins” → that is **not** sufficient for E45 promotion over D.

### Deliverables
- `repro/e45-c1-<date>/`  
- `research/e45/E45_C1_DECISION.md`  
- Updated `e45_status.json` (`PROMOTED` only after explicit approval)

---

## 2. G2 — How to complete the four-layer live engine

### Goal
One forward path that implements:

```
Signal(T) → Alpha sleeve orders + Core sleeve orders
         → Exact T+1 fill (E18)
         → E22 dividend cashflows
         → E45 exposure scales Alpha first, then Core if needed
```

### Method (ordered)

1. **Contract the capital split** (EXPERIMENTAL until approved)  
   - Default research split already tested: **80% core / 20% alpha** (`MIX_STATIC_80_20` best util on 2019–2026 overlap).  
   - Encode as config in a *new* forward package, e.g. `forward/e50_stack/` — **not** by rewriting `forward/e21/` history.

2. **State machine** (new script, read-only use of E21 market)  
   - States: `NORMAL | ALPHA_WEAK | CRISIS`  
   - Mapping: named E45 exposure + optional alpha trailing underperformance (pre-registered, OOF-only if used for selection).  
   - Actions:  
     - `ALPHA_WEAK` / partial crisis → cut alpha weight toward cash  
     - `CRISIS` → apply E45 scale to remaining equity; core membership unchanged unless E16 Crisis tilt says so  

3. **Ledger separation**  
   - `nav_core`, `nav_alpha`, `nav_combined`, `exposure_e45` daily  
   - Immutable append like E21 (`append_immutable`) so audit matches governance.

4. **Gate before “official path”**  
   - Paper parallel to E21 for N sessions  
   - QC: Exact T+1, no same-bar, cash non-negative, sleeve weights sum ≤ 1  

### Stop rules
- Do not merge into E21 until E45 promotion decision (G1) is at least “API locked”.  
- Do not use A3-R1 dual-gate PASS as a requirement for paper parallel — Option-2 already allows MIXED monitor.

### Deliverables
- `scripts/e50_stack_forward_pipeline.py`  
- `forward/e50_stack/` paper ledgers  
- QC JSON + comparison vs E21 core-only

---

## 3. G3 — How to get a promotable alpha (or stop)

### Goal
Either:

- a dual-gate (or governance-accepted MIXED) overlay worth freezing as E50-A_vN, **or**  
- an explicit stop: alpha remains paper/monitor forever on current data.

### Method (fork — pick one)

**Fork 3A — New information set (only high-EV research)**  
- Features/labels **outside** A2 family remix / TECH2–PRICE8.  
- Causal detectors from day one (`shift ≥ label horizon`).  
- Protocol: OOF → adversarial-lite → one-shot held-out → hard stop.  
- Bar: beat C4 (or 80/20 static mix) on util **and** stress; do not retune after held-out.

**Fork 3B — Accept Option-2 permanence**  
- C4 / S9A1 paper monitor with Stage-13 caveats.  
- No further panel grids.  
- Alpha sleeve in G2 uses **locked** A3-R1 (or C4) config as EXPERIMENTAL overlay capital only.

**Fork 3C — Governance gate reform** (not an alpha experiment)  
- Decide whether MIXED + stress MC ≈ 0.95 is enough for paper permanence.  
- Does not create a new model by itself.

### Stop rules
- No more top_k/reb/exit micro-grids.  
- No S9A1 cut retune.  
- No treating S9A1 as E45.

### Deliverables
- Either `repro/e50a-newinfo-<date>/` with PASS/MIXED decision, **or**  
- `GOVERNANCE_ALPHA_PANEL_SATURATED.md` declaring 3B.

---

## 4. G4 — True hedge layer (product decision first)

### Goal
Only if “股災也要賺／深度避險” remains a hard product requirement after G1–G2.

### Method
1. **Define hedge book separately** (third sleeve): e.g. cash + short index / put budget / inverse ETF — all EXPERIMENTAL.  
2. **Budget rule:** hedge notional ≤ X% of NAV; funded by cutting alpha first, then core tilt.  
3. **Evaluation:** crisis-window mean excess vs core+alpha without hedge; cost drag in bull regimes.  
4. **Promotion:** higher bar than alpha; never silent-add into E16 membership.

### Stop rules
- If G1 E45 de-lever already meets MDD policy, **do not** add shorts.  
- Four-layer results already show alpha MDD −50% — hedge research should target **alpha sleeve tail**, not rewrite core.

### Deliverables
- `research/e50_hedge/E50_HEDGE_CHARTER.md` before any code  
- Challenger sandbox only after charter sign-off

---

## 5. G5 — Wiring / data debts (parallel, cheaper)

| Item | How to close | Depends on |
|---|---|---|
| E22 → official E21 path | Challenger copy of fill loop + dividend credit; then promote E22 timing as new SOFT_FROZEN if approved | Low |
| A1 `available_date > effective_date` residuals | Data challenger rebuild with QC delta | HARD_FROZEN honesty |
| A0 industry master snapshot | Historical industry PIT source or documented limitation | HARD_FROZEN |
| E16 full-history live package | Promote reconstruction script behind `scripts/e16_*.py` API wrapping E21 constants | G2 |

These can run **in parallel** with G1; they should not block E45 verification.

---

## 6. Recommended sequence

```
P0  G1 E45-C1 verification + decision (A/B/C)
P0  G5 E22→NAV official challenger (cheap, already proven +4pp CAGR in sandbox)
P1  G2 four-layer paper forward (80/20 + alpha-cut-first) using locked alpha
P1  G3 choose 3A new-info OR 3B saturate declaration (do not do both half-way)
P2  G4 hedge sleeve only if product still requires crash PnL beyond E45
```

### What “done” looks like

| Gap | Done means |
|---|---|
| G1 | `e45_status.json` says promoted **or** explicit reject; −13.16% retired or verified |
| G2 | `forward/e50_stack/` paper-runs with QC PASS beside E21 |
| G3 | New-info held-out decision **or** written saturation stop |
| G4 | Charter + challenger **or** written “not required” |
| G5 | E22 on official path challenger merged or scheduled; data residuals ticketed |

---

## 7. Explicit non-goals

- In-place edit of E45 / E16 / E18 / E22 while still calling them the same frozen version  
- Promoting EXPERIMENTAL 2.5% / 0.70 gates to force PASS  
- More TECH2 family remix / cash-on-bull grids  
- Using S9A1 detector as crisis core  
- Claiming four-layer challenger util as production proof without paper parallel

---

## 8. Immediate next experiment (if executing)

**E45-C1 verified baseline + side-by-side vs V4.12-D** on the original raw/adjusted panels, writing `research/e45/e45_verified_baseline.json` and a promotion recommendation A/B/C.

That single step converts “missing official hedge core” from a naming problem into a **decidable** governance object.

---

## 9. Execution log (2026-09-04)

| Item | Result |
|---|---|
| E45-C1 vs D (PIT-reconstructed 12-stock panel) | **`B_KEEP_D_AS_BASELINE_E45_API_ONLY`** — MDD helps, return/Sharpe floor fail |
| Verified MDD artifact | `research/e45/e45_verified_baseline.json` (retires reliance on −13.16% text) |
| E22 official-path challenger | **`RECOMMEND_WIRE_E22_…_VIA_NEW_VERSION`** — CAGR +3.97 pp on E16 book |

Next P1: four-layer paper forward (`forward/e50_stack/`) using locked alpha + D/E45-API exposure signal; G3 choose new-info vs saturation.
