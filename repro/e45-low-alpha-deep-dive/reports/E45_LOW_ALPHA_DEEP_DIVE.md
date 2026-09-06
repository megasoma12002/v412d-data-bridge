# E45 PAPER Low-Alpha Deep-Dive (0.05–0.15)

Generated: `2026-09-06T01:33:57.134631+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.
Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.

## Roadmap context

- Priority **#1** on the E45 paper research list (dense band after fine grid; #2 crisis-triggered already run).
- Dense α: **0.05 / 0.08 / 0.10 / 0.12 / 0.15** (+ 0.00 BASE, + 0.25 observe ref).
- Profile: frozen `E3_VOLTARGET_WINNER` (not retuned).

## Held-out deltas vs BASE

| Book | α | MDD Δpp | CAGR giveback pp | Efficiency | Score | mean_exp |
|---|---:|---:|---:|---:|---:|---:|
| BLEND_E45_A05 | 0.05 | +0.85 | +1.07 | +0.80 | 0.320 | 0.995 |
| BLEND_E45_A08 | 0.08 | +0.96 | +1.33 | +0.73 | 0.302 | 0.993 |
| BLEND_E45_A10 | 0.10 | +0.95 | +1.60 | +0.60 | 0.153 | 0.991 |
| BLEND_E45_A12 | 0.12 | +0.88 | +1.85 | +0.47 | -0.048 | 0.989 |
| BLEND_E45_A15 | 0.15 | +0.79 | +2.06 | +0.38 | -0.241 | 0.986 |
| BLEND_E45_A25 | 0.25 | +0.63 | +2.83 | +0.22 | -0.783 | 0.977 |

## Sealed deltas vs BASE

| Book | α | MDD Δpp | CAGR giveback pp | Score |
|---|---:|---:|---:|---:|
| BLEND_E45_A15 | 0.15 | +4.65 | +2.94 | 3.179 |
| BLEND_E45_A12 | 0.12 | +4.23 | +2.52 | 2.968 |
| BLEND_E45_A25 | 0.25 | +5.13 | +4.36 | 2.944 |
| BLEND_E45_A10 | 0.10 | +3.88 | +2.19 | 2.787 |
| BLEND_E45_A08 | 0.08 | +3.43 | +1.78 | 2.544 |
| BLEND_E45_A05 | 0.05 | +3.07 | +1.50 | 2.317 |

**Held-out preferred:** `BLEND_E45_A05` (α=0.05) — MDD +0.85 / giveback +1.07

## Adjacent-α stability (held-out)

| From α | To α | Δ MDD pp | Δ giveback pp | Δ score |
|---:|---:|---:|---:|---:|
| 0.05 | 0.08 | +0.11 | +0.26 | -0.018 |
| 0.08 | 0.10 | -0.01 | +0.27 | -0.149 |
| 0.10 | 0.12 | -0.08 | +0.25 | -0.202 |
| 0.12 | 0.15 | -0.09 | +0.21 | -0.193 |

## Month-end PAUSE sensitivity (asof 2026-09-04)

Policy: ALERT >3pp / PAUSE_REVIEW >5pp CAGR giveback on YTD / trailing_1y.

| Book | α | Window | MDD Δpp | Giveback pp | Flag |
|---|---:|---|---:|---:|---|
| BASE_E16_E18_E22_v2s | 0.00 | trailing_1y | +0.00 | +0.00 | **OK** |
| BASE_E16_E18_E22_v2s | 0.00 | ytd | +0.00 | +0.00 | **OK** |
| BLEND_E45_A05 | 0.05 | trailing_1y | +3.07 | +5.62 | **PAUSE_REVIEW** |
| BLEND_E45_A05 | 0.05 | ytd | +3.07 | +5.00 | **PAUSE_REVIEW** |
| BLEND_E45_A08 | 0.08 | trailing_1y | +3.43 | +6.46 | **PAUSE_REVIEW** |
| BLEND_E45_A08 | 0.08 | ytd | +3.43 | +5.96 | **PAUSE_REVIEW** |
| BLEND_E45_A10 | 0.10 | trailing_1y | +3.88 | +7.29 | **PAUSE_REVIEW** |
| BLEND_E45_A10 | 0.10 | ytd | +3.88 | +6.75 | **PAUSE_REVIEW** |
| BLEND_E45_A12 | 0.12 | trailing_1y | +4.23 | +8.10 | **PAUSE_REVIEW** |
| BLEND_E45_A12 | 0.12 | ytd | +4.23 | +7.69 | **PAUSE_REVIEW** |
| BLEND_E45_A15 | 0.15 | trailing_1y | +4.65 | +8.84 | **PAUSE_REVIEW** |
| BLEND_E45_A15 | 0.15 | ytd | +4.65 | +8.44 | **PAUSE_REVIEW** |
| BLEND_E45_A25 | 0.25 | trailing_1y | +5.94 | +11.69 | **PAUSE_REVIEW** |
| BLEND_E45_A25 | 0.25 | ytd | +5.94 | +11.55 | **PAUSE_REVIEW** |

### Dense-band + observe-ref PAUSE clearance

| α | YTD | Trailing 1y | Both OK? |
|---:|---|---|---|
| 0.05 | PAUSE_REVIEW | PAUSE_REVIEW | NO |
| 0.08 | PAUSE_REVIEW | PAUSE_REVIEW | NO |
| 0.10 | PAUSE_REVIEW | PAUSE_REVIEW | NO |
| 0.12 | PAUSE_REVIEW | PAUSE_REVIEW | NO |
| 0.15 | PAUSE_REVIEW | PAUSE_REVIEW | NO |
| 0.25 | PAUSE_REVIEW | PAUSE_REVIEW | NO |

## Read-through (paper)

1. Held-out dense-band pick: **α=0.05** (+0.85 MDD / +1.07 giveback).
2. Use adjacent-α table to judge whether 0.05→0.15 is smooth or cliffy.
3. PAUSE clearance at current tip: **no dense α clears both YTD/1y PAUSE** at current tip — do not retarget observe on PAUSE grounds.
4. α=0.25 remains the operating blend observe sleeve until a new OPEN ballot.
5. This screen does **not** open/retarget observe or authorize stitch.

## Governance

- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**
- Live DEFAULT **`E22_v2s_tw` KEEP**
- Live E45 stitch **FORBIDDEN**
- −13.16% remains **RETIRED_HISTORICAL_NARRATIVE**

## Artifacts

- `/workspace/repro/e45-low-alpha-deep-dive/reports/e45_low_alpha_deep_dive.json`
- `/workspace/repro/e45-low-alpha-deep-dive/outputs/low_alpha_window_metrics.csv`
- `/workspace/repro/e45-low-alpha-deep-dive/outputs/low_alpha_deltas_vs_base.csv`
- `/workspace/repro/e45-low-alpha-deep-dive/outputs/low_alpha_adjacent_stability.csv`
- `/workspace/repro/e45-low-alpha-deep-dive/outputs/low_alpha_pause_sensitivity.csv`
- `/workspace/research/e45/E45_LOW_ALPHA_DEEP_DIVE.md`

## Reproduce

```bash
python3 scripts/e45_low_alpha_deep_dive_paper.py
```

