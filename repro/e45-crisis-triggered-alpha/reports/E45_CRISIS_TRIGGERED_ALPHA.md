# E45 PAPER Crisis-Triggered Alpha

Generated: `2026-09-06T01:19:55.834951+00:00`
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
| CONST_A05 | CONST | 0.05 | nan | heldout_2019_plus | +0.85 | +1.07 | 0.995 | 98.3% | 0.320 |
| CONST_A05 | CONST | 0.05 | nan | sealed_2023_plus | +3.07 | +1.50 | 0.995 | 98.3% | 2.317 |
| CONST_A05 | CONST | 0.05 | nan | full | +0.85 | +0.47 | 0.995 | 98.3% | n/a |
| CONST_A25 | CONST | 0.25 | nan | heldout_2019_plus | +0.63 | +2.83 | 0.977 | 98.3% | -0.783 |
| CONST_A25 | CONST | 0.25 | nan | sealed_2023_plus | +5.13 | +4.36 | 0.977 | 98.3% | 2.944 |
| CONST_A25 | CONST | 0.25 | nan | full | +0.63 | +1.38 | 0.977 | 98.3% | n/a |
| CONST_A100_FULL | CONST | 1.00 | nan | heldout_2019_plus | +1.88 | +5.65 | 0.907 | 98.3% | -0.943 |
| CONST_A100_FULL | CONST | 1.00 | nan | sealed_2023_plus | +4.90 | +9.40 | 0.907 | 98.3% | 0.195 |
| CONST_A100_FULL | CONST | 1.00 | nan | full | +1.88 | +2.99 | 0.907 | 98.3% | n/a |
| GATE_09_A25 | GATE | 0.25 | 0.9 | heldout_2019_plus | +0.26 | +1.23 | 0.987 | 25.3% | -0.352 |
| GATE_09_A25 | GATE | 0.25 | 0.9 | sealed_2023_plus | +2.29 | +2.04 | 0.987 | 25.3% | 1.274 |
| GATE_09_A25 | GATE | 0.25 | 0.9 | full | +0.26 | +0.63 | 0.987 | 25.3% | n/a |
| GATE_09_A50 | GATE | 0.50 | 0.9 | heldout_2019_plus | +0.33 | +1.77 | 0.974 | 25.3% | -0.552 |
| GATE_09_A50 | GATE | 0.50 | 0.9 | sealed_2023_plus | +2.43 | +2.79 | 0.974 | 25.3% | 1.032 |
| GATE_09_A50 | GATE | 0.50 | 0.9 | full | +0.33 | +0.92 | 0.974 | 25.3% | n/a |
| GATE_09_A100 | GATE | 1.00 | 0.9 | heldout_2019_plus | +0.40 | +3.16 | 0.949 | 25.3% | -1.175 |
| GATE_09_A100 | GATE | 1.00 | 0.9 | sealed_2023_plus | +3.21 | +4.73 | 0.949 | 25.3% | 0.841 |
| GATE_09_A100 | GATE | 1.00 | 0.9 | full | +0.40 | +1.67 | 0.949 | 25.3% | n/a |
| GATE_085_A25 | GATE | 0.25 | 0.85 | heldout_2019_plus | +0.15 | +1.17 | 0.990 | 14.6% | -0.429 |
| GATE_085_A25 | GATE | 0.25 | 0.85 | sealed_2023_plus | +2.01 | +1.89 | 0.990 | 14.6% | 1.063 |
| GATE_085_A25 | GATE | 0.25 | 0.85 | full | +0.15 | +0.61 | 0.990 | 14.6% | n/a |
| GATE_085_A50 | GATE | 0.50 | 0.85 | heldout_2019_plus | +0.20 | +1.66 | 0.981 | 14.6% | -0.630 |
| GATE_085_A50 | GATE | 0.50 | 0.85 | sealed_2023_plus | +2.09 | +2.51 | 0.981 | 14.6% | 0.839 |
| GATE_085_A50 | GATE | 0.50 | 0.85 | full | +0.20 | +0.89 | 0.981 | 14.6% | n/a |
| GATE_085_A100 | GATE | 1.00 | 0.85 | heldout_2019_plus | +0.32 | +2.99 | 0.962 | 14.6% | -1.173 |
| GATE_085_A100 | GATE | 1.00 | 0.85 | sealed_2023_plus | +3.13 | +4.27 | 0.962 | 14.6% | 0.993 |
| GATE_085_A100 | GATE | 1.00 | 0.85 | full | +0.32 | +1.60 | 0.962 | 14.6% | n/a |
| GATE_08_A25 | GATE | 0.25 | 0.8 | heldout_2019_plus | +0.07 | +0.92 | 0.993 | 7.9% | -0.388 |
| GATE_08_A25 | GATE | 0.25 | 0.8 | sealed_2023_plus | +1.69 | +1.42 | 0.993 | 7.9% | 0.978 |
| GATE_08_A25 | GATE | 0.25 | 0.8 | full | +0.07 | +0.49 | 0.993 | 7.9% | n/a |
| GATE_08_A50 | GATE | 0.50 | 0.8 | heldout_2019_plus | +0.11 | +1.38 | 0.987 | 7.9% | -0.578 |
| GATE_08_A50 | GATE | 0.50 | 0.8 | sealed_2023_plus | +1.87 | +2.01 | 0.987 | 7.9% | 0.862 |
| GATE_08_A50 | GATE | 0.50 | 0.8 | full | +0.11 | +0.74 | 0.987 | 7.9% | n/a |
| GATE_08_A100 | GATE | 1.00 | 0.8 | heldout_2019_plus | +0.21 | +2.67 | 0.974 | 7.9% | -1.128 |
| GATE_08_A100 | GATE | 1.00 | 0.8 | sealed_2023_plus | +3.11 | +3.65 | 0.974 | 7.9% | 1.286 |
| GATE_08_A100 | GATE | 1.00 | 0.8 | full | +0.21 | +1.43 | 0.974 | 7.9% | n/a |
| E1BIN_A25 | E1BIN | 0.25 | nan | heldout_2019_plus | +0.00 | +0.14 | 0.999 | 1.2% | -0.070 |
| E1BIN_A25 | E1BIN | 0.25 | nan | sealed_2023_plus | +0.43 | +0.13 | 0.999 | 1.2% | 0.366 |
| E1BIN_A25 | E1BIN | 0.25 | nan | full | +0.00 | +0.08 | 0.999 | 1.2% | n/a |
| E1BIN_A50 | E1BIN | 0.50 | nan | heldout_2019_plus | +0.00 | +0.34 | 0.997 | 1.2% | -0.168 |
| E1BIN_A50 | E1BIN | 0.50 | nan | sealed_2023_plus | +0.81 | +0.42 | 0.997 | 1.2% | 0.595 |
| E1BIN_A50 | E1BIN | 0.50 | nan | full | +0.00 | +0.18 | 0.997 | 1.2% | n/a |
| E1BIN_A100 | E1BIN | 1.00 | nan | heldout_2019_plus | +0.00 | +1.06 | 0.994 | 1.2% | -0.531 |
| E1BIN_A100 | E1BIN | 1.00 | nan | sealed_2023_plus | +2.49 | +1.54 | 0.994 | 1.2% | 1.716 |
| E1BIN_A100 | E1BIN | 1.00 | nan | full | +0.00 | +0.57 | 0.994 | 1.2% | n/a |

## Held-out ranking (score = MDD_pp − 0.5·|CAGR_giveback_pp|)

**Preferred (held-out):** `CONST_A05` (mode=CONST, α=0.05, gate=nan) — MDD ~+0.85 pp / giveback ~+1.07 pp

### Top 5 held-out

| Rank | Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | CONST_A05 | CONST | 0.05 | nan | +0.85 | +1.07 | 0.320 |
| 2 | E1BIN_A25 | E1BIN | 0.25 | nan | +0.00 | +0.14 | -0.070 |
| 3 | E1BIN_A50 | E1BIN | 0.50 | nan | +0.00 | +0.34 | -0.168 |
| 4 | GATE_09_A25 | GATE | 0.25 | 0.9 | +0.26 | +1.23 | -0.352 |
| 5 | GATE_08_A25 | GATE | 0.25 | 0.8 | +0.07 | +0.92 | -0.388 |

### Best by mode (held-out)

- **GATE**: `GATE_09_A25` — MDD +0.26 / giveback +1.23 / score -0.352
- **CONST**: `CONST_A05` — MDD +0.85 / giveback +1.07 / score 0.320
- **E1BIN**: `E1BIN_A25` — MDD +0.00 / giveback +0.14 / score -0.070

## Sealed top-3 (same score)

| Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| CONST_A25 | CONST | 0.25 | nan | +5.13 | +4.36 | 2.944 |
| CONST_A05 | CONST | 0.05 | nan | +3.07 | +1.50 | 2.317 |
| E1BIN_A100 | E1BIN | 1.00 | nan | +2.49 | +1.54 | 1.716 |

## Read-through (paper)

1. **Held-out winner remains low constant α:** `CONST_A05` (~+0.85 MDD / ~1.07 giveback) beats every `GATE` / `E1BIN` book on the heuristic score.
2. **Deep-cut gates lose MDD more than they save giveback** on held-out: best gate `GATE_09_A25` only ~+0.26 MDD vs ~1.23 giveback (score −0.35).
3. **E1 binary gate is too sparse (~1.2% days):** held-out MDD improve ≈ **0**; sealed can look better (`E1BIN_A100` ~+2.49 MDD) but is not a held-out challenger.
4. **Sealed still likes continuous moderate overlay** (`CONST_A25` tops sealed score) — same tension as the fine grid (held-out low-α vs sealed mid-α).
5. **Paper path:** keep studying **low constant α** (and existing observe sleeves); do **not** promote crisis-gated α from this screen.
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

