# Soft-Frozen Clip Search — Stage B

Generated: `2026-09-07T17:42:13.139271+00:00`
Ballot: **ACCEPT clip-search charter** · Soft-Frozen **KEEP**
Execution: capital **5,000,000** · lot **1000** · `E22_v2s_tw`
Mode: `fin_locked_floors_hi_soft_frozen` · challengers ok **19**
Status: **STAGE_B_CANDIDATES_LOCKED**

## BASE (Soft-Frozen control)

- held-out MDD `-0.23305299070914165` · CAGR `0.18403341057399403`
- sealed MDD `-0.14470194442933482`

## Top-K by held-out score (sealed report-only)

| id | heldout score | MDD↑pp | CAGRΔpp | sealed MDD↑pp | fragile? |
|---|---:|---:|---:|---:|---|
| `CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.05-0.35` | 0.396 | 0.562 | 0.331 | 0.833 | False |
| `CLIP_SEARCH_F0.50-0.95_T0.10-0.35_E0.00-0.35` | 0.349 | 0.665 | 0.632 | 1.082 | False |
| `CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.00-0.35` | 0.294 | 0.459 | 0.329 | 0.430 | False |

## Hard rules

- Soft-Frozen live module untouched
- Sealed not used for selection
- Passing ≠ Class D Soft-Frozen flip

Repro: `repro/clip-search-20260907/`
