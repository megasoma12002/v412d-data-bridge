# FIN_SAT_TIPGAP_PRED_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:31:00Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

Tip-gap prediction: leading IC · tip vs held contrast · cycle overlap · ≤3 IC-gated probes.

## Leading IC (fwd_rel_21)

| feat | IC | \|IC\| | signHit | gate | sat_when_high |
|---|---:|---:|---:|---|---|
| r0050_63_l1 | -0.1094 | 0.1094 | 0.5379 | True | True |
| zz08_bear_l1 | -0.0855 | 0.0855 | 0.5307 | True | True |
| mdd0050_63_l1 | -0.0757 | 0.0757 | 0.4694 | False | True |
| crisis_l1 | 0.0671 | 0.0671 | 0.5121 | False | False |
| zz12_bear_l1 | 0.0652 | 0.0652 | 0.4912 | False | False |
| vol0050_21_l1 | 0.0511 | 0.0511 | 0.4989 | False | False |
| trail_rel_63_l1 | -0.0454 | 0.0454 | 0.511 | False | True |
| comp_sells_21_l1 | -0.0425 | 0.0425 | 0.5187 | False | True |
| trail_rel_21_l1 | -0.0384 | 0.0384 | 0.5072 | False | True |
| month_sin_l1 | 0.0347 | 0.0347 | 0.5151 | False | False |
| month_cos_l1 | -0.0212 | 0.0212 | 0.5121 | False | True |
| bearcrisis_l1 | 0.0128 | 0.0128 | 0.5154 | False | False |

## Tip1y − held feature contrast

```json
{
  "crisis": 0.043267,
  "bearcrisis": -0.055129,
  "zz08_bear": 0.051094,
  "mdd0050_63": 0.002157,
  "r0050_63": 0.138536,
  "vol0050_21": 0.004554,
  "trail_rel_63": -0.013667,
  "comp_sells_21": 1.861838,
  "trail_drag": 0.241274,
  "rel": -0.000302,
  "pct_trail_drag": 24.13
}
```

## Cycle overlap on tip-drag days

```json
{
  "tip_drag_base_rate": 69.42,
  "n_tip": 242,
  "crisis": {
    "n": 48,
    "drag_rate": 100.0,
    "lift_pp": 30.58
  },
  "bearcrisis": {
    "n": 48,
    "drag_rate": 100.0,
    "lift_pp": 30.58
  },
  "zz08_bear": {
    "n": 53,
    "drag_rate": 60.38,
    "lift_pp": -9.04
  },
  "zz12_bear": {
    "n": 11,
    "drag_rate": 100.0,
    "lift_pp": 30.58
  },
  "sells21_hi": {
    "n": 114,
    "drag_rate": 87.72,
    "lift_pp": 18.3
  },
  "rel63_neg": {
    "n": 168,
    "drag_rate": 100.0,
    "lift_pp": 30.58
  }
}
```

## Worst COMP-lag months

| month | rel_sum_pp | crisis% | zz08% | sells21 |
|---|---:|---:|---:|---:|
| 2015-08 | -4.594 | 85.71 | 95.24 | 64.14 |
| 2022-09 | -4.364 | 100.0 | 80.95 | 40.14 |
| 2026-06 | -3.649 | 0.0 | 0.0 | 6.95 |
| 2026-09 | -2.26 | 0.0 | 0.0 | 32.17 |
| 2018-05 | -2.135 | 0.0 | 100.0 | 76.0 |
| 2016-05 | -2.129 | 66.67 | 61.9 | 42.48 |
| 2026-02 | -2.127 | 0.0 | 0.0 | 5.75 |
| 2021-11 | -2.065 | 0.0 | 0.0 | 16.14 |

## Books / probes

| ID | fam | heldCAGR↑ | tipCAGR↑ | tipClean | HIT |
|---|---|---:|---:|---|---|
| CTRL_LIVE_A10 | ctrl | -0.0 | 0.0 | True | False |
| REF_SAT_RELAX | ref | 0.3343 | 0.6801 | True | False |
| REF_COMP_H150_A20 | ref | 0.5415 | -13.3591 | False | False |
| PRB_R0050_63 | switch | 1.0925 | -3.3781 | False | False |
| PRB_ZZ08_BEAR | switch | 1.7476 | -17.0269 | False | False |

## Recommendation

```json
{
  "binding_gap": "tip_cagr_drag_timing",
  "best_leading_feat": "r0050_63_l1",
  "best_ic": -0.1094,
  "ic_gate_feats": [
    "r0050_63_l1",
    "zz08_bear_l1"
  ],
  "tip_vs_held_highlights": {
    "trail_rel_63": -0.013667,
    "comp_sells_21": 1.861838,
    "vol0050_21": 0.004554,
    "crisis": 0.043267,
    "zz08_bear": 0.051094,
    "pct_trail_drag": 24.13
  },
  "cycle_overlap_tip": {
    "tip_drag_base_rate": 69.42,
    "n_tip": 242,
    "crisis": {
      "n": 48,
      "drag_rate": 100.0,
      "lift_pp": 30.58
    },
    "bearcrisis": {
      "n": 48,
      "drag_rate": 100.0,
      "lift_pp": 30.58
    },
    "zz08_bear": {
      "n": 53,
      "drag_rate": 60.38,
      "lift_pp": -9.04
    },
    "zz12_bear": {
      "n": 11,
      "drag_rate": 100.0,
      "lift_pp": 30.58
    },
    "sells21_hi": {
      "n": 114,
      "drag_rate": 87.72,
      "lift_pp": 18.3
    },
    "rel63_neg": {
      "n": 168,
      "drag_rate": 100.0,
      "lift_pp": 30.58
    }
  },
  "note": "Prefer features that lead fwd_rel_21 and lift tip-drag overlap; do not return to calendar year switch."
}
```

Verdict: **`TIP_MDD_ONLY`**

Label: `FIN_SAT_TIPGAP_PRED_STAGEA_SCREEN_2026-09-28__TIP_MDD_ONLY`
