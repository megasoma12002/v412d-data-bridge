# FIN_CAP_50 — Sealed-CAGR Improve Charter

Date: 2026-09-05  
Status: **CHARTER OPEN for research** — RESEARCH_ONLY; no live-wire; Soft-Frozen stays **[0.50, 0.95]**.  
Authority: `research/STRATEGY_DEBT_BOARD.md` · five-layer Layer 1 OPEN item

## Parent artifacts (do not invent)

| Artifact | Role |
|---|---|
| `research/gaps/FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.md` | Exact T+1 candidate screen (sealed diagnostic only) |
| `research/gaps/MDD_L4_PATH_FINCAP_CHARTER.md` | Frozen L4 family screen (Crisis-only / FIN70 / Blend / DD-path) |
| `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md` | Authoritative go-live: **`NOT_READY_SEALED_CAGR`** |
| `research/ops/CUTOVER_CHECKLIST_FIN50.md` | Human cutover gates (still red) |

## Problem statement

FIN_CAP_50 dual-paper is **OPERATING**, but cutover stays frozen because **sealed 2023+ CAGR giveback** (~4.1–4.3 pp) fails live-aware gates. Trailing 1y / YTD also PAUSE.

This charter exists so Layer-1 “FIN50 sealed CAGR gate OPEN” has an explicit research path — **not** a silent Soft-Frozen flip.

## Non-negotiables

1. Soft-Frozen Financial clip **[0.50, 0.95]** stays until a separate human cutover PR.  
2. Do **not** retune the FIN_CAP_50 lock `[0.35, 0.50]` in place.  
3. Do **not** reopen L1/L2/L3 STOPPED locks.  
4. Dual-paper FIN_CAP_50 month-end continues as observation only.  
5. Sealed window may be used for **gates / diagnostics**, never as the sole selection window.

## Research vehicle

Use the already-frozen **L4 path / mild-FIN families** as the sealed-CAGR improve vehicle:

| Family | Why it is in scope |
|---|---|
| L4-CRISIS-ONLY | Keeps Soft-Frozen finance beta in non-crisis bull |
| L4-FINCAP-70 | Milder static than FIN50 / L3_60 |
| L4-BLEND-LIGHT | Partial concentration (α∈{0.25,0.50}) |
| L4-DD-PATH | Path DD trigger (already dual-paper OPERATING as L4_DD_PATH_08_50) |

Static FIN_CAP_50 remains the **blocked reference**, not a retune target.

## Pass gates (pre-declare)

A challenger may advance to **paper promote proposal** only if all hold:

| Gate | Threshold |
|---|---|
| Exact T+1 | Hard |
| OOF MDD improve vs BASE | ≥ **1.0 pp** |
| OOF / late-bull CAGR giveback | ≤ **1.5 pp** |
| Sealed CAGR giveback vs BASE | ≤ **3.0 pp** |
| Sealed MDD improve | ≥ **1.0 pp** |
| Trailing 1y / YTD vs BASE | Not PAUSE_REVIEW (or documented waiver) |

Passing gates ≠ live cutover. Cutover still requires `CUTOVER_CHECKLIST_FIN50.md` all-green + human PR.

## Out of scope

- Soft-Frozen auto-flip  
- Live-wiring any L4 / FIN70 / blend without checklist  
- Treating dual-paper PASS / held-out PASS as cutover license  
- Reopening Stage-8 / S1 residual grids  

## Exit criteria for this charter

| Outcome | Action |
|---|---|
| Named challenger clears sealed gates | Dual-paper observe + promote proposal only |
| No family clears sealed ≤3.0 pp | Charter → **STOP**; keep FIN50 dual-paper; Soft-Frozen KEEP |
| Human rejects promote | Stay dual-paper; do not reopen locks |

## Ops linkage (five-layer)

| Layer | Effect of this charter |
|---|---|
| L1 Strategy | Converts “FIN50 sealed CAGR OPEN” from vague debt → **named research path** |
| L2 Ops | No cadence change; month-end pack still authoritative for PAUSE |
| L3 Data | Unchanged |
| L4 Governance | Cutover checklist remains the only promote door |
| L5 Eng | No Soft-Frozen constant edit |

## Commands / pointers

```bash
# diagnostic (already landed)
python3 scripts/fincap_sealed_cagr_improve_diag.py

# L4 dual-paper / month-end (observation)
python3 scripts/ops_month_end_paper_pack.py
```

Soft-Frozen clip source: `scripts/e16_soft_frozen_base.py` (`SOFT_FROZEN_FIN_LO/HI`).
