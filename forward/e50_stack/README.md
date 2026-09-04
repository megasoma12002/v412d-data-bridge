# E50 Stack Paper Forward

**Status:** `PAPER_EXPERIMENTAL` — does not modify `forward/e21/`.

## Contract

- Core 80% / Alpha 20% (EXPERIMENTAL)
- Core = E16 + Exact T+1 + E22 dividends
- E45 = signal only → alpha-cut-first (decision **B**)
- Alpha = locked A3-R1 (Option-2 MIXED)

## QC

`PASS` — checks: `{"nav_unique_date": true, "state_unique_date": true, "nav_positive": true, "date_monotonic": true, "sleeve_weights_sum_le_one": true, "exposure_in_unit_interval": true, "states_valid": true, "audit_unique_date": true, "audit_chain_links": true, "exact_t1_core": true, "no_same_bar_core": true}`

## Paper window

`2019-01-02` → `2026-08-28` (1851 days)

| Metric | Value |
|---|---:|
| CAGR | 14.88% |
| MDD | -23.13% |
| Util | 0.03316467221202468 |

State counts: `{'ALPHA_WEAK': 926, 'NORMAL': 470, 'CRISIS': 455}`

## Explicit non-actions

- No E45 promotion
- No alpha promotion
- No in-place E21 rewrite
