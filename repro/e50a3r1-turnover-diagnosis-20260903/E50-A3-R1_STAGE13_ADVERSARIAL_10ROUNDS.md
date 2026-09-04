# Stage-13 Adversarial 10-Round Review (Option-2 / S9A1)

**Protocol:** falsify paper-monitor claims. No E45 edit. No S9A1 retune. No gate promotion.

## Overall: `OPTION2_KEEP_PAPER_MONITOR_WITH_ADVERSARIAL_CAVEATS`

Worst round verdict: **WOUNDED**

| Round | Attack | Verdict |
|---|---|---|
| 1 Leakage / look-ahead | Detector uses val_ic_lag21 from trailing_ic with only shift(1); fwd_21… | `WOUNDED` |
| 2 Placebo freeze | Matched-frequency random freeze calendar on VAL.… | `SURVIVES` |
| 3 Scrambled months | Permute monthly detector mass within VAL while preserving monthly on-c… | `SURVIVES` |
| 4 Subperiod fragility | Calendar-year util/excess S9A1 vs C4 on VAL and SEALED.… | `SURVIVES` |
| 5 Higher slippage | Re-simulate identical signals under 2x/3x/5x BASE_SLIPPAGE.… | `SURVIVES` |
| 6 EW-crisis vs detector | Compare excess on EW crisis_vote2 days vs COMBO_VOL70_VAL03 detector d… | `WOUNDED` |
| 7 Bootstrap sensitivity | Vary block length and RNG seed for block-bootstrap P(excess>0) on VAL.… | `WOUNDED` |
| 8 Sealed autopsy | Month-level S9A1−C4 excess on SEALED; compare aggregate edges.… | `SURVIVES` |
| 9 Capacity / liquidity | Raise liquidity_floor 2x/5x/10x and half-scale gross exposure.… | `SURVIVES` |
| 10 Selection bias | Inventory of searched challengers; multiple-testing narrative on stres… | `SURVIVES` |

## Key quantitative hits

- R1 published VAL stress edge vs C4: `0.0007770435301989302`
- R1 causal-IC VAL stress edge vs C4: `0.0006344391103360531`
- R1 causal-IC VAL util / boot: `0.0302` / `0.4254` (published `0.0855` / `0.6232`)
- R1 flag overlap published∩causal: `26` / `97`
- R2 P(placebo stress ≥ S9A1): `0.1` (util beat rate `0.0`)
- R3 P(scramble stress ≥ S9A1): `0.13333333333333333`
- R6 detector∩EW-crisis days on VAL: `0` / `97` (crisis days `62`)
- R7 VAL boot range across block/seed grid: `0.492`–`0.671`
- R8 sealed util edge S9−C4: `0.0932` (month-ahead share `0.48`)

## Required caveats (Option-2 still stands)

- Do not treat published val_ic_lag21 as live-tradable without shift>=21 (label horizon); causal rebuild collapses VAL util 0.086->0.030 and boot 0.62->0.43.
- Detector is orthogonal to EW crisis_vote2 by construction (0/97 overlap on VAL); it is not a crash overlay substitute for E45.
- VAL bootstrap remains MIXED and sensitive to block length (range ~0.18 across grid); never promote 0.70 gate.
- S9A1 stays paper/monitor only; C4 remains research baseline; E45 untouched.

## Operating implication

Keep Option-2 **paper/monitor** with the caveats above. Still `MIXED`. Still not frozen. Still not an E45 replacement.

For any live monitor feed, rebuild the detector with **strictly causal** value-IC (`shift >= 21` on raw IC before the rolling mean). Do not ship the published `val_ic_lag21` definition as-of-T.

Artifact: `reports/stage13_adversarial_10rounds_summary.json`
