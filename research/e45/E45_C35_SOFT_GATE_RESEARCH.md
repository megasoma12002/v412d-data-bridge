# E45 C35 Soft Regime-Gate — Recover Held-out

Generated: `2026-09-08T03:51:49.879673+00:00`
Goal: keep tip **PASS/PASS** while recovering held-out score lost by hard Bear+Crisis gate.
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged

Ungated C35 held-out `+1.807` · Hard Bear+Crisis `+0.715`

| Book | days on | held score | recovery* | sealed | YTD gb | YTD | 1y gb | 1y | tip clean | non2020 |
|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|
| `M2_RELOC_BIL_FX_C35` | 100.0% | +1.807 | +1.00 | -0.375 | +7.56 | **PAUSE_REVIEW** | +4.76 | **ALERT** | False | 3 |
| `M2_C35_HARD_BEAR_CRISIS` | 23.3% | +0.715 | +0.00 | -0.845 | +1.94 | **PASS** | +0.32 | **PASS** | True | 3 |
| `M2_C35_SOFT_A` | 31.7% | +0.829 | +0.11 | -0.880 | +1.98 | **PASS** | +0.18 | **PASS** | True | 3 |
| `M2_C35_SOFT_B` | 31.7% | +0.669 | -0.04 | -0.908 | +2.35 | **PASS** | +0.63 | **PASS** | True | 3 |
| `M2_C35_SOFT_SIDE40` | 31.7% | +0.189 | -0.48 | -0.950 | +3.33 | **ALERT** | +1.00 | **PASS** | False | 3 |
| `M2_C35_SOFT_BEAR50` | 23.3% | +0.040 | -0.62 | -0.901 | +1.82 | **PASS** | +0.04 | **PASS** | True | 2 |
| `M2_C35_SOFT_CRISIS50_HARD` | 23.3% | +0.194 | -0.48 | -1.005 | +4.65 | **ALERT** | +2.25 | **PASS** | False | 3 |
| `M2_C35_SOFT_CRISIS_BOOST` | 31.7% | +0.139 | -0.53 | -1.069 | +6.45 | **PAUSE_REVIEW** | +3.51 | **ALERT** | False | 3 |
| `M2_C35_SOFT_A_C40` | 31.7% | +0.545 | -0.16 | -0.919 | +2.93 | **PASS** | +0.93 | **PASS** | True | 3 |
| `M2_C35_HYST_K10` | 31.5% | +0.958 | +0.22 | -1.201 | +3.70 | **ALERT** | +1.70 | **PASS** | False | 3 |

\* recovery = (score − hard) / (ungated − hard); 1.0 = fully back to ungated.

## Year MDD help pp

| Book | 2015 | 2018 | 2020 | 2022 |
|---|---:|---:|---:|---:|
| `M2_RELOC_BIL_FX_C35` | +1.65 | +0.69 | +2.52 | +4.56 |
| `M2_C35_HARD_BEAR_CRISIS` | +1.17 | +0.53 | +0.79 | +5.06 |
| `M2_C35_SOFT_A` | +1.33 | +0.28 | +0.93 | +4.67 |
| `M2_C35_SOFT_B` | +1.17 | +0.53 | +0.79 | +5.00 |
| `M2_C35_SOFT_SIDE40` | +1.33 | +0.26 | +0.35 | +4.57 |
| `M2_C35_SOFT_BEAR50` | +1.00 | +0.22 | +0.16 | +4.35 |
| `M2_C35_SOFT_CRISIS50_HARD` | +1.53 | +0.43 | +0.53 | +5.79 |
| `M2_C35_SOFT_CRISIS_BOOST` | +1.53 | +0.43 | +0.53 | +5.79 |
| `M2_C35_SOFT_A_C40` | +1.49 | +0.34 | +0.67 | +5.08 |
| `M2_C35_HYST_K10` | +1.47 | +0.74 | +1.34 | +4.99 |

## How to improve the sacrificed long-term score

Root cause: hard gate drops **2020 MDD help** `+2.52 → +0.79` pp; score = MDD↑ − 0.5·|CAGR giveback|.
Same-family (C35 × Soft-Frozen regime) cannot restore ungated `+1.81` **and** keep tip PASS.

- **Best tip-clean recovery:** `M2_C35_SOFT_A` · gap closed `+0.11` (only ~11%).
- Tip-dirty books that beat Soft_A on held-out: `['M2_C35_HYST_K10']` (e.g. hysteresis K10) — **not** eligible while tip hygiene is binding.
- Stronger Sideways / higher cut / Crisis-boost either **dirties tip** or **lowers** held-out.

### Remaining improve paths (outside this screen)

1. **Ballot** `ACCEPT observe retarget Soft_A` (paper only) — small held-out lift, tip still PASS.
2. **Dual monitor** — keep ungated C35 for long-score observe; track Soft_A/HARD as tip-hygiene twin.
3. **New mechanism** — leave C35×regime (cheap-protect, tax-control, other actuator).
4. **Accept tradeoff** — live path prioritizes tip PASS; held-out ~0.8 is the cost of the gate.

## Verdict

- Tip-clean books: `['M2_C35_HARD_BEAR_CRISIS', 'M2_C35_SOFT_A', 'M2_C35_SOFT_B', 'M2_C35_SOFT_BEAR50', 'M2_C35_SOFT_A_C40']`
- Tip-clean **and** held-out ≥ hard: `['M2_C35_SOFT_A', 'M2_C35_HARD_BEAR_CRISIS']`
- Best recover: `M2_C35_SOFT_A` · gap closed `+0.11`
- Same-family soft gates **do not** close most of the hard-gate score gap.

Repro: `repro/e45-c35-soft-gate-20260908/`
