# E45 Sideways-Conditional Gate — Research

Generated: `2026-09-08T07:43:05.781483+00:00`
Goal: tip **PASS** and held-out **> Soft_A** via conditional Sideways (not mult grid).
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged

Soft_A held-out `+0.829` · Hard `+0.715` · Ungated `+1.807`

| Book | kind | days on | held | recovery | sealed | YTD gb | YTD | 1y gb | 1y | tip | 2020 |
|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|
| `M2_RELOC_BIL_FX_C35` | ungated | 100.0% | +1.807 | +1.00 | -0.375 | +7.56 | **PAUSE_REVIEW** | +4.76 | **ALERT** | False | +2.52 |
| `M2_C35_HARD_BEAR_CRISIS` | hard | 23.3% | +0.715 | +0.00 | -0.845 | +1.94 | **PASS** | +0.32 | **PASS** | True | +0.79 |
| `M2_C35_SOFT_A` | soft_a | 31.7% | +0.829 | +0.11 | -0.880 | +1.98 | **PASS** | +0.18 | **PASS** | True | +0.93 |
| `M2_C35_SIDE_CONT` | side_cont | 23.4% | +0.184 | -0.49 | -1.158 | +1.82 | **PASS** | -0.04 | **PASS** | True | +0.35 |
| `M2_C35_SIDE_HIGH_S80` | side_high_s80 | 25.1% | +0.229 | -0.44 | -0.788 | +2.30 | **PASS** | +0.62 | **PASS** | True | +0.35 |
| `M2_C35_SIDE_DD05` | side_dd05 | 23.5% | +0.320 | -0.36 | -0.837 | +1.81 | **PASS** | +0.10 | **PASS** | True | +0.35 |
| `M2_C35_SIDE_DD10` | side_dd10 | 23.3% | +0.166 | -0.50 | -1.297 | +2.39 | **PASS** | +0.31 | **PASS** | True | +0.35 |
| `M2_C35_SIDE_MAX10` | side_max10 | 26.0% | +0.795 | +0.07 | -0.912 | +2.17 | **PASS** | +0.21 | **PASS** | True | +0.93 |
| `M2_C35_SIDE_MAX20` | side_max20 | 27.2% | +0.829 | +0.10 | -0.862 | +2.08 | **PASS** | +0.21 | **PASS** | True | +0.93 |

## Verdict

- Tip-clean challengers: `['M2_C35_SIDE_CONT', 'M2_C35_SIDE_HIGH_S80', 'M2_C35_SIDE_DD05', 'M2_C35_SIDE_DD10', 'M2_C35_SIDE_MAX10', 'M2_C35_SIDE_MAX20']`
- Tip-clean **and** beat Soft_A: `[]`
- Best tip-clean challenger: `M2_C35_SIDE_MAX20`
- Residue closed (no Soft_A beater)? **True**

Repro: `repro/e45-sideways-conditional-20260908/`
