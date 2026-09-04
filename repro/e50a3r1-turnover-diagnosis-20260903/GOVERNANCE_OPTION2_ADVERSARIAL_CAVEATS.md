# Option-2 — Adversarial Caveats (Stage-13)

Date: 2026-09-04
Source: Stage-13 adversarial 10-round review

## Decision unchanged

Option-2 remains: **C4** research baseline; **S9A1** paper/monitor only; **E45** untouched; gates not promoted.

## What the red-team changed

Option-2 is **not withdrawn**, but monitor operations must carry these caveats:

1. **Causal detector** — published `val_ic_lag21` only shifts IC by 1 day while labels are 21d forward. A strict causal rebuild keeps a partial stress edge but collapses VAL utility (~0.086→~0.030) and bootstrap (~0.62→~0.43). Live paper feed must use causal IC.
2. **Not a crash overlay** — on VAL, detector ∩ EW `crisis_vote2` = **0/97** days. S9A1 does not replace E45.
3. **Bootstrap fragile / MIXED** — official VAL boot ~0.62; block/seed grid spans ~0.49–0.67. Never treat as dual-gate PASS.
4. **Placebo/scramble did not kill timing** — random matched freezes rarely beat S9A1 util (0/20); stress beat rate ~10–13%. Timing content survives, subject to (1).

Label: `GOVERNANCE_OPTION2_ADVERSARIAL_CAVEATS_ACCEPTED`

## Auto-iterate follow-up (axis CAUSAL_VALUE_IC_S9A1)

Ran locked-cut causal twin **S9A1C** through OOF → adv-lite.

| Step | Result |
|---|---|
| L1 OOF | dual-gate PASS (util≈S9A1, boot 0.76) |
| L2 adv-lite | **FALSIFIED** — VAL util vs C4 = −0.027; placebo P(util≥)=0.67 |
| L3 held-out | skipped (hard stop) |

**Decision:** `KEEP_PUBLISHED_S9A1_CAUSAL_ADV_FAIL` / `STOP_ADV_FALSIFIED`

Implication: causal IC remains a **honesty** requirement for any live feed interpretation, but the causal twin is **not** a performance upgrade and must **not** replace the Option-2 archive S9A1 metrics. **Stop this axis** — do not retune cuts.
