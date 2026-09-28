# FIN_SAT_DIV_EPISODE_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T14:02:05Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

Label COMP−SAT divergence episodes (trail_rel_63 ±θ, K=5), contrast features **inside** episodes.

## Coverage by θ

| θ | %SAT_LEAD | %COMP_LEAD | %SIMILAR | n_SAT_ep | n_COMP_ep |
|---:|---:|---:|---:|---:|---:|
| 0.01 | 21.69 | 24.01 | 54.29 | 30 | 32 |
| 0.02 | 10.82 | 9.3 | 79.88 | 15 | 17 |

## Contrast θ=0.01 (SAT_LEAD − SIMILAR)

```json
{
  "crisis": 0.16529,
  "bearcrisis": 0.209503,
  "r0050_63": -0.014226,
  "mdd0050_63": -0.015563,
  "vol0050_21": 0.001252,
  "comp_sells_21": 6.754526,
  "zz08_bear": -0.001151
}
```

## Contrast θ=0.01 (SAT_LEAD − COMP_LEAD)

```json
{
  "crisis": 0.112516,
  "bearcrisis": 0.117208,
  "r0050_63": 0.009671,
  "mdd0050_63": -0.001356,
  "vol0050_21": 0.001747,
  "comp_sells_21": 9.096223,
  "zz08_bear": 0.079818
}
```

## Leading IC → next-day SAT_LEAD

| feat | IC | hit | gate | sat_when_high |
|---|---:|---:|---|---|
| crisis_l1 | 0.1853 | 0.7625 | True | True |
| bearcrisis_l1 | 0.1734 | 0.7087 | True | True |
| comp_sells_21_l1 | 0.1382 | 0.566 | True | True |
| vol0050_21_l1 | 0.1111 | 0.5197 | False | True |
| mdd0050_63_l1 | -0.0847 | 0.5394 | True | False |
| zz08_bear_l1 | 0.0291 | 0.6902 | False | True |
| r0050_63_l1 | -0.027 | 0.5103 | False | False |

## Probes

| ID | heldCAGR↑ | tipCAGR↑ | tipClean | HIT |
|---|---:|---:|---|---|
| CTRL_LIVE_A10 | -0.0 | 0.0 | True | False |
| REF_SAT_RELAX | 0.3343 | 0.6801 | True | False |
| REF_COMP_H150_A20 | 0.5415 | -13.3591 | False | False |
| PRB_STATE_SAT_LEAD | 1.6984 | -6.701 | False | False |
| PRB_CRISIS | -0.3302 | -18.7345 | False | False |

Verdict: **`TIP_MDD_ONLY`**

Label: `FIN_SAT_DIV_EPISODE_STAGEA_SCREEN_2026-09-28__TIP_MDD_ONLY`
