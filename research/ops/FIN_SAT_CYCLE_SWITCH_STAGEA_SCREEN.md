# FIN_SAT_CYCLE_SWITCH_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:25:18Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false** · **not year-switch**

Cycle switches: ZigZag half-cycle · regime confirm K=5 · month/quarter REL · HIT tip-clean+held+vsSAT.

## Regime-episode summary (not calendar year)

```json
{
  "Bear": {
    "n_episodes": 19,
    "mean_len": 16.9,
    "comp_win_rate": 42.1,
    "mean_comp_minus_sat_pp": 0.053
  },
  "Bull": {
    "n_episodes": 32,
    "mean_len": 75.6,
    "comp_win_rate": 37.5,
    "mean_comp_minus_sat_pp": -0.184
  },
  "Crisis": {
    "n_episodes": 11,
    "mean_len": 36.3,
    "comp_win_rate": 45.5,
    "mean_comp_minus_sat_pp": -0.002
  },
  "Sideways": {
    "n_episodes": 7,
    "mean_len": 12.3,
    "comp_win_rate": 28.6,
    "mean_comp_minus_sat_pp": -0.42
  }
}
```

## Books

| ID | fam | %SAT | flips | cycles~ | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| CTRL_LIVE_A10 | ctrl | 0.0 | 0 | 0 | -0.0 | 0.0 | True | False | False |
| REF_SAT_RELAX | ref | 100.0 | 0 | 0 | 0.3343 | 0.6801 | True | False | False |
| REF_COMP_H150_A20 | ref | 0.0 | 0 | 0 | 0.5415 | -13.3591 | False | True | False |
| SW_ZZ08_BEAR_SAT | switch | 18.01 | 36 | 18 | 1.7476 | -17.0269 | False | True | False |
| SW_ZZ12_BEAR_SAT | switch | 8.71 | 18 | 9 | 0.5491 | -12.761 | False | True | False |
| SW_CRISIS_K5 | switch | 12.45 | 18 | 9 | 0.2889 | -13.0042 | False | False | False |
| SW_BEARCRISIS_K5 | switch | 23.3 | 34 | 17 | 0.026 | -13.0042 | False | False | False |
| SW_MONTH_REL63 | switch | 43.48 | 45 | 22 | 0.1324 | -7.0588 | False | False | False |
| SW_QTR_REL126 | switch | 48.68 | 15 | 7 | 0.0103 | -3.279 | False | False | False |

Verdict: **`TIP_MDD_ONLY`**

Label: `FIN_SAT_CYCLE_SWITCH_STAGEA_SCREEN_2026-09-28__TIP_MDD_ONLY`
