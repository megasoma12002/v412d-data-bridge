# FIN_CAP_50 Sealed-CAGR Charter Screen

Generated: `2026-09-07T17:21:03.190753+00:00`
Status: **RESEARCH_ONLY** — Soft-Frozen **[0.50, 0.95] KEEP**; no cutover.

## Decision: **HIST_PASS_TRAIL_FAIL**

STOP for promote — hist gates clear for some families but trailing FAIL; keep FIN50 dual-paper; Soft-Frozen KEEP.

### Hist-pass IDs (OOF / late-bull / sealed)

- `FIN_CAP_70_STATIC`
- `BLEND_025`
- `BLEND_050`
- `CRISIS_ONLY_50`

### Promote-eligible (hist + trailing)

- None

### Operating dual-paper trailing

- FIN_CAP_50 pause/cutover_blocked: **True** / **True**
- L4_DD_PATH_08_50 pause/cutover_blocked: **True** / **True**

### Family table

| Family | Member | Hist pass | Trail pass | Charter pass |
|---|---|---|---|---|
| `L4-CRISIS-ONLY` | `CRISIS_ONLY_50` | True | False | False |
| `L4-FINCAP-70` | `FIN_CAP_70_STATIC` | True | False | False |
| `L4-BLEND-LIGHT` | `BLEND_025` | True | False | False |
| `L4-BLEND-LIGHT` | `BLEND_050` | True | False | False |
| `L4-DD-PATH` | `DD_BEAR_CRISIS_50` | False | False | False |

## Hard rules

- Do not retune FIN_CAP_50 lock
- Do not Soft-Frozen flip
- Passing charter ≠ live cutover

Re-run: `python3 scripts/fincap50_sealed_cagr_charter_screen.py`
