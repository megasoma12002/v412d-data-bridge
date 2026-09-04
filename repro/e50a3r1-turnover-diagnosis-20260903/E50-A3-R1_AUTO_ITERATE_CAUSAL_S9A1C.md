# Auto-Iterate Ledger — Causal Value-IC S9A1 (S9A1C)

**Axis:** `CAUSAL_VALUE_IC_S9A1` — locked cuts; only IC causality fixed.
No E45 edit. No cut retune. No gate promotion. No portfolio micro-grid.

## Decision: `KEEP_PUBLISHED_S9A1_CAUSAL_ADV_FAIL`

Stop reason: `STOP_ADV_FALSIFIED`

## L1 OOF

- L1 pass: `True` dual-gate causal: `True`
- Flag days OOF published/causal: `231` / `214`
- C4 util/boot: `-0.05922310146239623` / `0.703`
- S9A1 util/boot/stress: `-0.05485240238998851` / `0.737` / `0.0003207064491405518`
- S9A1C util/boot/stress: `-0.05430841737272679` / `0.7602` / `-3.727960844552165e-05`

## L2 Adversarial-lite

- Placebo P(util≥): `0.6666666666666666` P(stress≥): `0.4166666666666667`
- VAL years beat C4 util: `['2021']`
- VAL edge util/stress vs C4: `-0.02701539618842208` / `0.0006344391103360531`
- Falsified/wounded: `True` / `False`

## L3 Held-out

_(skipped)_

## Operating implication

Do not replace S9A1 with causal twin for now; keep Option-2 caveats. Stop this axis.

Artifact: `reports/auto_iterate_ledger.json`
