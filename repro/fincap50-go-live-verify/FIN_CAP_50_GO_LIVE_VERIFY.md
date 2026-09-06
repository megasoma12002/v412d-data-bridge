# FIN_CAP_50 Go-Live Research Verification

Generated: `2026-09-05T17:50:46.605362+00:00`
As-of: `2026-09-04`
Status: **RESEARCH_ONLY** — Soft-Frozen live clip **not** changed.

## Decision: `NOT_READY_SEALED_CAGR`

Research decision: `GO_LIVE_VERIFY_BLOCKED_SEALED_CAGR__KEEP_SOFT_FROZEN`

### Gates

| Gate | Rule | Result |
|---|---|---|
| A Exact T+1 | both books | PASS |
| B Held-out 2019+ | MDD≥1pp & CAGR gb≤3pp | PASS (MDD +3.06pp; CAGR gb +1.63pp) |
| C Sealed 2023+ | MDD≥1pp & CAGR gb≤3pp | FAIL (MDD +4.41pp; CAGR gb +4.33pp) |
| D Soft-Frozen | stays [0.50, 0.95] | PASS |
| E Month-end | no PAUSE_REVIEW | FAIL |

### Windows

| Window | BASE CAGR | BASE MDD | FIN50 CAGR | FIN50 MDD | MDD Δpp | CAGR gb pp | PASS |
|---|---:|---:|---:|---:|---:|---:|---|
| heldout_2019_plus | 18.24% | -22.64% | 16.60% | -19.58% | +3.06 | +1.63 | Y |
| validation_2019_2022 | 12.33% | -22.64% | 13.08% | -19.58% | +3.06 | -0.75 | Y |
| sealed_2023_plus | 24.93% | -14.46% | 20.59% | -10.04% | +4.41 | +4.33 | N |

### Month-end alerts

- `PAUSE_REVIEW` on `trailing_1y` — {'window': 'trailing_1y', 'level': 'PAUSE_REVIEW', 'cagr_giveback_pp': 7.211901866269743}
- `PAUSE_REVIEW` on `ytd` — {'window': 'ytd', 'level': 'PAUSE_REVIEW', 'cagr_giveback_pp': 16.72890298607934}

## Aftermath

- **Do not cut over live.** Soft-Frozen stays **[0.50, 0.95]**.
- Continue dual-paper month-end observation only.
- If blocked on sealed CAGR: new charter required (do not retune FIN_CAP_50 lock).

Artifacts:
- `/workspace/repro/fincap50-go-live-verify/reports/fincap50_go_live_verify.json`
