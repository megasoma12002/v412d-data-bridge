# FIN Concentration — Sealed CAGR Improvement Diagnostics

Generated: `2026-09-05T03:22:41.675088+00:00`
As-of: `2026-09-04`
Status: **RESEARCH_ONLY** — no Soft-Frozen edit; sealed used diagnostically only.

## Problem

FIN_CAP_50 / L3 static mild caps clear combined 2019+ or OOF, but **sealed 2023+ CAGR giveback** fails live-aware gates (~4.1–4.3 pp). Go-live verify also tripped PAUSE_REVIEW on trailing windows.

## Candidates (Exact T+1)

| ID | Family | OOF MDDΔ | OOF CAGRgb | Late-bull gb | Sealed MDDΔ | Sealed CAGRgb | Sealed diag | Sel-safe |
|---|---|---:|---:|---:|---:|---:|---|---|
| BASE | baseline | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | — | — |
| FIN_CAP_50_REF | blocked_static_ref | +4.57 | +0.35 | +1.26 | +4.41 | +4.33 |  | Y |
| L3_MILD_35_60_REF | failed_l3_static_ref | +2.88 | +0.10 | +0.15 | +5.29 | +4.08 |  | Y |
| FIN_CAP_70_STATIC | milder_static | +1.71 | -0.05 | -0.50 | +5.05 | +1.75 | Y | Y |
| BLEND_025 | static_blend | +1.37 | +0.03 | +0.40 | +2.11 | +0.51 | Y | Y |
| BLEND_050 | static_blend | +2.83 | -0.00 | +0.65 | +4.68 | +1.18 | Y | Y |
| BULL_RESTORE_50 | path_conditional | +2.19 | +0.12 | +1.20 | +3.21 | +3.69 |  | Y |
| BULL_RESTORE_60 | path_conditional | +0.67 | +0.13 | +0.74 | +3.17 | +2.17 | Y |  |
| DD_BEAR_CRISIS_50 | path_conditional | +2.19 | +0.11 | +1.15 | +0.51 | +2.33 |  | Y |
| CRISIS_ONLY_50 | path_conditional | +1.31 | -0.01 | +0.22 | +1.06 | +0.93 | Y | Y |

### Selection-safe (OOF MDD≥1 & OOF/late CAGR gb≤1.5)

- Count: **8** → `['FIN_CAP_50_REF', 'L3_MILD_35_60_REF', 'FIN_CAP_70_STATIC', 'BLEND_025', 'BLEND_050', 'BULL_RESTORE_50', 'DD_BEAR_CRISIS_50', 'CRISIS_ONLY_50']`
- Of which sealed-diag PASS: **4** → `['FIN_CAP_70_STATIC', 'BLEND_025', 'BLEND_050', 'CRISIS_ONLY_50']`

## Implications

1. Static FIN caps (50/60) improve MDD but leak sealed CAGR in 2024–2026 bull stretch.
2. Path-conditional caps (Bull-restore / Crisis-only) aim to keep Soft-Frozen finance beta in Bull while cutting only in stress.
3. Do not retune FIN_CAP_50 / L3_MILD_35_60 locks; screen new path-conditional family under a frozen L4 charter.
4. Soft-Frozen live stays [0.50, 0.95] until human cutover after sealed-aware PASS.

## Recommended next research

Freeze **L4 path-conditional FIN charter**: Bull-restore / Crisis-only / true DD-path first.
Do **not** retune FIN_CAP_50 or L3_MILD_35_60. Soft-Frozen stays [0.50, 0.95].

See: `research/gaps/MDD_L4_PATH_FINCAP_CHARTER.md`
