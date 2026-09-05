# FINCAP L4-BLEND-025 — Dual-Paper Promote Proposal (NOT LIVE)

Date: 2026-09-05  
Status: **PROPOSAL ONLY — dual-paper observe candidate**  
Screen: `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`  
Charter: `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`

## Decision from charter screen

| Item | Value |
|---|---|
| Family | L4-BLEND-LIGHT |
| ID | **BLEND_025** (α=0.25·FIN50 + 0.75·Soft-Frozen BASE) |
| Hist gates | **PASS** (OOF MDD / OOF+late CAGR gb / sealed MDD+CAGR) |
| Trailing ytd / 1y | **PASS** (ytd gb ≈ 2.48 pp; trailing_1y gb ≈ 0.29 pp) |
| Screen decision | **`PAPER_PROMOTE_PROPOSAL_ONLY`** |

## What this does NOT authorize

- Soft-Frozen clip flip (stays **[0.50, 0.95]**)
- Live cutover / live-wire
- Retune of FIN_CAP_50 lock `[0.35, 0.50]`
- Closing FIN50 dual-paper (still OPERATING / `NOT_READY_SEALED_CAGR`)

## Proposed next ops step (human-gated)

1. Open **dual-paper observe sleeve** for `BLEND_025` beside BASE Soft-Frozen (Exact T+1).  
2. Include in month-end pack as observe-only.  
3. Re-check charter trailing gates each month-end.  
4. Live cutover only after `CUTOVER_CHECKLIST_FIN50.md` green + human PR (separate).

## Operating context (still blocked)

| Sleeve | Trailing | Cutover |
|---|---|---|
| FIN_CAP_50 dual-paper | PAUSE_REVIEW | FROZEN (`NOT_READY_SEALED_CAGR`) |
| L4_DD_PATH_08_50 dual-paper | PAUSE_REVIEW | FROZEN |

## Reproducers

```bash
python3 scripts/fincap50_sealed_cagr_charter_screen.py
# artifacts:
#   research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.{json,md}
#   repro/fincap50-sealed-cagr-charter-screen/
```
