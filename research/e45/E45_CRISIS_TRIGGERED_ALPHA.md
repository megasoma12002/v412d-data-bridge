# E45 PAPER Crisis-Triggered Alpha

Generated: `2026-09-06T05:13:29.643124+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.
Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.

## Why this screen

- Constant blend α still cuts mild-vol days (E3_exp < 1 on ~98% of sample).
- Fine grid preferred **low constant α (~0.05)** on held-out.
- Question: can gating α to **deeper-cut / crisis states** keep MDD help with less CAGR giveback?

## Definitions

| Mode | Rule |
|---|---|
| `CONST` | `exposure = (1−α)·1 + α·E45` |
| `GATE` | if `E45_exp ≥ gate` → `1.0`; else constant-α blend |
| `E1BIN` | if E1 binary crisis → constant-α blend; else `1.0` |

- Profile: `E3_VOLTARGET_WINNER` (frozen; not retuned)
- Gate day fractions (full sample): `<0.9` ≈ 25.3%, `<0.85` ≈ 14.6%, `<0.8` ≈ 7.9%
- E1 binary crisis fraction: ≈ **1.19%**

## Focus deltas vs BASE

| Book | Mode | α | Gate | Window | MDD Δpp | CAGR giveback pp | mean_exp | frac_days<1 | score |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| BLEND_E45_A05 | CONST | 0.05 | nan | heldout_2019_plus | +0.70 | +0.96 | 0.995 | 98.3% | 0.222 |
| BLEND_E45_A05 | CONST | 0.05 | nan | sealed_2023_plus | +2.78 | +1.42 | 0.995 | 98.3% | 2.069 |
| BLEND_E45_A05 | CONST | 0.05 | nan | full | +0.70 | +0.42 | 0.995 | 98.3% | n/a |
| BLEND_E45_A25 | CONST | 0.25 | nan | heldout_2019_plus | +0.45 | +2.72 | 0.977 | 98.3% | -0.908 |
| BLEND_E45_A25 | CONST | 0.25 | nan | sealed_2023_plus | +4.75 | +4.32 | 0.977 | 98.3% | 2.595 |
| BLEND_E45_A25 | CONST | 0.25 | nan | full | +0.45 | +1.33 | 0.977 | 98.3% | n/a |
| CHAL_E45_E3 | CONST | 1.00 | nan | heldout_2019_plus | +1.71 | +5.41 | 0.907 | 98.3% | -0.996 |
| CHAL_E45_E3 | CONST | 1.00 | nan | sealed_2023_plus | +4.54 | +9.03 | 0.907 | 98.3% | 0.025 |
| CHAL_E45_E3 | CONST | 1.00 | nan | full | +1.71 | +2.88 | 0.907 | 98.3% | n/a |
| GATE_09_A25 | GATE | 0.25 | 0.9 | heldout_2019_plus | +0.18 | +1.14 | 0.987 | 25.3% | -0.392 |
| GATE_09_A25 | GATE | 0.25 | 0.9 | sealed_2023_plus | +2.21 | +1.95 | 0.987 | 25.3% | 1.235 |
| GATE_09_A25 | GATE | 0.25 | 0.9 | full | +0.18 | +0.60 | 0.987 | 25.3% | n/a |
| GATE_09_A50 | GATE | 0.50 | 0.9 | heldout_2019_plus | +0.26 | +1.73 | 0.974 | 25.3% | -0.605 |
| GATE_09_A50 | GATE | 0.50 | 0.9 | sealed_2023_plus | +2.33 | +2.78 | 0.974 | 25.3% | 0.945 |
| GATE_09_A50 | GATE | 0.50 | 0.9 | full | +0.26 | +0.91 | 0.974 | 25.3% | n/a |
| GATE_09_A100 | GATE | 1.00 | 0.9 | heldout_2019_plus | +0.34 | +2.93 | 0.949 | 25.3% | -1.125 |
| GATE_09_A100 | GATE | 1.00 | 0.9 | sealed_2023_plus | +2.93 | +4.29 | 0.949 | 25.3% | 0.790 |
| GATE_09_A100 | GATE | 1.00 | 0.9 | full | +0.34 | +1.55 | 0.949 | 25.3% | n/a |
| GATE_085_A25 | GATE | 0.25 | 0.85 | heldout_2019_plus | +0.13 | +1.11 | 0.990 | 14.6% | -0.428 |
| GATE_085_A25 | GATE | 0.25 | 0.85 | sealed_2023_plus | +1.99 | +1.85 | 0.990 | 14.6% | 1.070 |
| GATE_085_A25 | GATE | 0.25 | 0.85 | full | +0.13 | +0.59 | 0.990 | 14.6% | n/a |
| GATE_085_A50 | GATE | 0.50 | 0.85 | heldout_2019_plus | +0.17 | +1.64 | 0.981 | 14.6% | -0.652 |
| GATE_085_A50 | GATE | 0.50 | 0.85 | sealed_2023_plus | +2.06 | +2.49 | 0.981 | 14.6% | 0.815 |
| GATE_085_A50 | GATE | 0.50 | 0.85 | full | +0.17 | +0.88 | 0.981 | 14.6% | n/a |
| GATE_085_A100 | GATE | 1.00 | 0.85 | heldout_2019_plus | +0.29 | +2.78 | 0.962 | 14.6% | -1.098 |
| GATE_085_A100 | GATE | 1.00 | 0.85 | sealed_2023_plus | +2.86 | +3.86 | 0.962 | 14.6% | 0.927 |
| GATE_085_A100 | GATE | 1.00 | 0.85 | full | +0.29 | +1.50 | 0.962 | 14.6% | n/a |
| GATE_08_A25 | GATE | 0.25 | 0.8 | heldout_2019_plus | +0.05 | +0.92 | 0.993 | 7.9% | -0.407 |
| GATE_08_A25 | GATE | 0.25 | 0.8 | sealed_2023_plus | +1.75 | +1.45 | 0.993 | 7.9% | 1.027 |
| GATE_08_A25 | GATE | 0.25 | 0.8 | full | +0.05 | +0.50 | 0.993 | 7.9% | n/a |
| GATE_08_A50 | GATE | 0.50 | 0.8 | heldout_2019_plus | +0.12 | +1.42 | 0.987 | 7.9% | -0.590 |
| GATE_08_A50 | GATE | 0.50 | 0.8 | sealed_2023_plus | +1.91 | +2.04 | 0.987 | 7.9% | 0.891 |
| GATE_08_A50 | GATE | 0.50 | 0.8 | full | +0.12 | +0.78 | 0.987 | 7.9% | n/a |
| GATE_08_A100 | GATE | 1.00 | 0.8 | heldout_2019_plus | +0.21 | +2.48 | 0.974 | 7.9% | -1.034 |
| GATE_08_A100 | GATE | 1.00 | 0.8 | sealed_2023_plus | +2.81 | +3.25 | 0.974 | 7.9% | 1.188 |
| GATE_08_A100 | GATE | 1.00 | 0.8 | full | +0.21 | +1.33 | 0.974 | 7.9% | n/a |
| E1BIN_A25 | E1BIN | 0.25 | nan | heldout_2019_plus | +0.00 | +0.14 | 0.999 | 1.2% | -0.071 |
| E1BIN_A25 | E1BIN | 0.25 | nan | sealed_2023_plus | +0.33 | +0.16 | 0.999 | 1.2% | 0.254 |
| E1BIN_A25 | E1BIN | 0.25 | nan | full | +0.00 | +0.08 | 0.999 | 1.2% | n/a |
| E1BIN_A50 | E1BIN | 0.50 | nan | heldout_2019_plus | +0.00 | +0.34 | 0.997 | 1.2% | -0.170 |
| E1BIN_A50 | E1BIN | 0.50 | nan | sealed_2023_plus | +0.73 | +0.38 | 0.997 | 1.2% | 0.547 |
| E1BIN_A50 | E1BIN | 0.50 | nan | full | +0.00 | +0.18 | 0.997 | 1.2% | n/a |
| E1BIN_A100 | E1BIN | 1.00 | nan | heldout_2019_plus | +0.00 | +0.99 | 0.994 | 1.2% | -0.495 |
| E1BIN_A100 | E1BIN | 1.00 | nan | sealed_2023_plus | +2.16 | +1.47 | 0.994 | 1.2% | 1.429 |
| E1BIN_A100 | E1BIN | 1.00 | nan | full | +0.00 | +0.53 | 0.994 | 1.2% | n/a |

## Held-out ranking (score = MDD_pp − 0.5·|CAGR_giveback_pp|)

**Preferred (held-out):** `BLEND_E45_A05` (mode=CONST, α=0.05, gate=nan) — MDD ~+0.70 pp / giveback ~+0.96 pp

### Top 5 held-out

| Rank | Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | BLEND_E45_A05 | CONST | 0.05 | nan | +0.70 | +0.96 | 0.222 |
| 2 | E1BIN_A25 | E1BIN | 0.25 | nan | +0.00 | +0.14 | -0.071 |
| 3 | E1BIN_A50 | E1BIN | 0.50 | nan | +0.00 | +0.34 | -0.170 |
| 4 | GATE_09_A25 | GATE | 0.25 | 0.9 | +0.18 | +1.14 | -0.392 |
| 5 | GATE_08_A25 | GATE | 0.25 | 0.8 | +0.05 | +0.92 | -0.407 |

### Best by mode (held-out)

- **GATE**: `GATE_09_A25` — MDD +0.18 / giveback +1.14 / score -0.392
- **CONST**: `BLEND_E45_A05` — MDD +0.70 / giveback +0.96 / score 0.222
- **E1BIN**: `E1BIN_A25` — MDD +0.00 / giveback +0.14 / score -0.071

## Sealed top-3 (same score)

| Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| BLEND_E45_A25 | CONST | 0.25 | nan | +4.75 | +4.32 | 2.595 |
| BLEND_E45_A05 | CONST | 0.05 | nan | +2.78 | +1.42 | 2.069 |
| E1BIN_A100 | E1BIN | 1.00 | nan | +2.16 | +1.47 | 1.429 |

## Read-through (paper)

1. **Held-out winner remains low constant α:** `BLEND_E45_A05` beats gated / E1BIN books on the heuristic score.
2. **Deep-cut gates lose MDD more than they save giveback** on held-out vs `BLEND_E45_A05`.
3. **E1 binary gate is too sparse (~1.2% days)** for held-out MDD help (often ≈0).
4. **Sealed may still favor continuous moderate overlay** — same held-out vs sealed tension as the fine grid.
5. **Paper path:** keep **low constant α**; do **not** promote crisis-gated α from this screen.
6. This screen does **not** open a new observe sleeve or authorize stitch.

## Governance

- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**
- Live DEFAULT **`E22_v2s_tw` KEEP**
- Live E45 stitch **FORBIDDEN**
- −13.16% remains **RETIRED_HISTORICAL_NARRATIVE**

## Artifacts

- `/workspace/repro/e45-crisis-triggered-alpha/reports/e45_crisis_triggered_alpha.json`
- `/workspace/repro/e45-crisis-triggered-alpha/outputs/crisis_triggered_window_metrics.csv`
- `/workspace/repro/e45-crisis-triggered-alpha/outputs/crisis_triggered_deltas_vs_base.csv`
- `/workspace/research/e45/E45_CRISIS_TRIGGERED_ALPHA.md`

## Reproduce

```bash
python3 scripts/e45_crisis_triggered_alpha_paper.py
```

