# FIN_CAP_50 Sealed-CAGR Charter Screen

Generated: `2026-09-05T08:01:17.243710+00:00`
Status: **RESEARCH_ONLY** — Soft-Frozen **[0.50, 0.95] KEEP**; no cutover.

## Decision: **PAPER_PROMOTE_PROPOSAL_ONLY**

Named challenger may enter dual-paper observe + promote proposal only (not live cutover).

### Hist-pass IDs (OOF / late-bull / sealed)

- `FIN_CAP_70_STATIC`
- `BLEND_025`
- `BLEND_050`
- `CRISIS_ONLY_50`

### Promote-eligible (hist + trailing)

- `L4-BLEND-LIGHT` / `BLEND_025`

### Operating dual-paper trailing

- FIN_CAP_50 pause/cutover_blocked: **True** / **True**
- L4_DD_PATH_08_50 pause/cutover_blocked: **True** / **True**

### Family table

| Family | Member | Hist pass | Trail pass | Charter pass |
|---|---|---|---|---|
| `L4-CRISIS-ONLY` | `CRISIS_ONLY_50` | True | False | False |
| `L4-FINCAP-70` | `FIN_CAP_70_STATIC` | True | False | False |
| `L4-BLEND-LIGHT` | `BLEND_025` | True | True | True |
| `L4-BLEND-LIGHT` | `BLEND_050` | True | False | False |
| `L4-DD-PATH` | `DD_BEAR_CRISIS_50` | False | False | False |

## Hard rules

- Do not retune FIN_CAP_50 lock
- Do not Soft-Frozen flip
- Passing charter ≠ live cutover

Re-run: `python3 scripts/fincap50_sealed_cagr_charter_screen.py`
