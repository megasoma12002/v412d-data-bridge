# E45 Four-Path Recover — Research

Generated: `2026-09-08T04:31:23.180058+00:00`
Ballot: **四條路都研究** · Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**
Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`**

Baseline gap: ungated held-out `+1.807` · hard `+0.715` · Soft_A `+0.829`

## All books (held-out × tip)

| Book | family | held score | recovery* | sealed | YTD gb | YTD | 1y gb | 1y | tip | non2020 |
|---|---|---:|---:|---:|---:|---|---:|---|---|---:|
| `M2_RELOC_BIL_FX_C35` | C35_x_regime | +1.807 | +1.00 | -0.375 | +7.56 | **PAUSE_REVIEW** | +4.76 | **ALERT** | False | 3 |
| `M2_C35_HARD_BEAR_CRISIS` | C35_x_regime | +0.715 | +0.00 | -0.845 | +1.94 | **PASS** | +0.32 | **PASS** | True | 3 |
| `M2_C35_SOFT_A` | C35_x_regime | +0.829 | +0.11 | -0.880 | +1.98 | **PASS** | +0.18 | **PASS** | True | 3 |
| `M2_C35_INTEN_Q70` | C35_intensity_gate_no_regime | +0.196 | -0.47 | -1.662 | +6.96 | **PAUSE_REVIEW** | +4.37 | **ALERT** | False | 2 |
| `M2_C35_INTEN_Q80` | C35_intensity_gate_no_regime | +0.894 | +0.16 | -1.640 | +6.39 | **PAUSE_REVIEW** | +3.45 | **ALERT** | False | 2 |
| `M2_C35_INTEN_Q90` | C35_intensity_gate_no_regime | -0.571 | -1.18 | -0.855 | +0.44 | **PASS** | -0.33 | **PASS** | True | 2 |
| `BLEND_E45_A05` | cheap_protect_e45_exposure | +0.096 | -0.57 | +0.450 | +1.86 | **PASS** | +1.91 | **PASS** | True | 0 |
| `SLEEVE_FIN_ONLY_A10` | cheap_protect_e45_exposure | +0.316 | -0.37 | +0.812 | +2.98 | **PASS** | +2.80 | **PASS** | True | 0 |
| `M3_STATE_V0` | M3_three_state | -1.718 | -2.23 | +1.768 | +7.47 | **PAUSE_REVIEW** | +5.58 | **PAUSE_REVIEW** | False | 0 |

\* recovery = (score − hard) / (ungated − hard).

## Path 1 — Soft_A observe retarget (DRAFT ballot)

- Current lock: `M2_RELOC_BIL_FX_C35` · tip `PAUSE_REVIEW/ALERT` · held `+1.807`
- Proposed: `M2_C35_SOFT_A` · tip `PASS/PASS` · held `+0.829`
- Δ held-out vs lock: `-0.978` (expected drop vs ungated; gain vs hard `+0.115`)
- Status: **DRAFT ONLY** — not OPEN; needs human ACCEPT to swap observe lock.
- Live wire / Soft-Frozen / stitch: **No**.

## Path 2 — Dual monitor

- **Long-score twin:** `M2_RELOC_BIL_FX_C35` (held `+1.807`, tip dirty expected).
- **Tip-hygiene twin (primary):** `M2_C35_SOFT_A` (held `+0.829`, tip PASS).
- **Tip-hygiene twin (strict):** `M2_C35_HARD_BEAR_CRISIS` (held `+0.715`, tip PASS).
- Ops: Month-end: report long-score twin held-out/sealed deltas AND tip twin YTD/1y gates. Do not auto-flip observe lock. Promote/stitch still requires separate ACCEPT.
- Conflict: If long-score twin tip is PAUSE/ALERT while tip twin is PASS: expected under this design; do not treat long-score tip dirt as Soft_A failure.

## Path 3 — New mechanism (outside C35×regime soft-mult)

- Screened: `['M2_C35_INTEN_Q70', 'M2_C35_INTEN_Q80', 'M2_C35_INTEN_Q90', 'BLEND_E45_A05', 'SLEEVE_FIN_ONLY_A10', 'M3_STATE_V0']`
- Tip-clean: `['M2_C35_INTEN_Q90', 'BLEND_E45_A05', 'SLEEVE_FIN_ONLY_A10']`
- Tip-clean & ≥ hard: `[]`
- Tip-clean & **beat Soft_A**: `[]`
- Verdict: **`NO_PATH3_BEATS_SOFT_A_WHILE_TIP_CLEAN`**

## Path 4 — Accept tip-PASS tradeoff

- Buy: tip YTD giveback `+7.56 → +1.94` pp (hard) / Soft_A `+1.98`.
- Pay: held-out `+1.807 → +0.715` (hard) or `+0.829` (Soft_A); 2020 MDD help `+2.52 → +0.79`.
- Stance: **`ACCEPT_TRADEOFF_IS_VALID_DEFAULT_IF_TIP_BINDING`** when tip is binding and Path3 has no Soft_A beater.

## Integrated verdict

- Best tip-clean overall: `M2_C35_SOFT_A`
- Path3 replaces Soft_A? **False**
- Recommended stack: `['KEEP_or_ACCEPT_Soft_A_for_tip_hygiene', 'DUAL_MONITOR_ungated_for_long_score', 'CONTINUE_new_mechanism_ladder_outside_C35_x_regime', 'ACCEPT_tradeoff_if_tip_binding_and_no_Path3_winner']`

Repro: `repro/e45-four-path-recover-20260908/`
