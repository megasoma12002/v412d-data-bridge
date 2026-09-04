# Stage-3 Research Summary

Draft only. **No retune of C2/C4/C8. No promotion. No E45. PR #19 stays draft.**

## 1. Deep 2021–2022 excess autopsy (no retune)

Shared failure across **C2 / C4 / C8** vs PIT proxy:

| Finding | Detail |
|---|---|
| Weak years | 2021–2022 mean excess negative; other val years positive (C4: −0.00031 vs +0.00045) |
| Common bad months | **13** months where all three refs have negative excess |
| Worst months | 2022-05, 2022-08, 2021-06 (large negative monthly excess) |
| Regime split | Weak-year loss concentrated in **RISK_ON**; RISK_OFF ~flat |
| Turnover/cost | Slightly higher in weak years; not enough alone to explain bootstrap fail |
| Crowding / industry | Still electronics/semiconductor-heavy; portfolio micro-diffs do not remove the shared months |

**Implication:** failure is alpha/regime-period shared, not C4 vs C2 vs C8 rule noise.

Artifact: `E50-A3-R1_STAGE3_2021_2022_AUTOPSY.md`

## 2. New feature families × regime definitions (OOF only)

Fixed portfolio: **C4 wrapper**. Selection window: **2011–2018 OOF only**.

| Axis | Values screened |
|---|---|
| Features | TECH2 (baseline), VALUE2, QUALITY2, GROWTH2, VAL_MOM, QUAL_VAL, FAMILY3, FAMILY5 |
| Regimes | BREADTH_BASE, BREADTH_STRICT55, BREADTH_21, TREND_ONLY, VOL_REGIME |
| Mode | mostly BREADTH_REGIME (+ GLOBAL probes) |

**Decision: `OOF_NO_NEW_FEATURE_REGIME_DUAL_GATE_WINNER`**

| Finding | Detail |
|---|---|
| Dual-gate survivors | Only TECH2 + BREADTH_BASE (and TREND_ONLY twin) |
| TREND_ONLY | **Degenerate**: 0/1972 OOF days disagree vs BREADTH_BASE — excluded, not FR1 |
| Non-degenerate regimes | STRICT55 / BREADTH_21 / VOL all fail OOF bootstrap for TECH2 and new families |
| New families | VALUE2/QUALITY2/…/FAMILY5: IC sometimes ok, bootstrap collapses (often ≪0.5) |

Do **not** held-out TREND_ONLY. Do **not** retune C2/C4/C8.

Artifact: `E50-A3-R1_STAGE3_FEATURE_REGIME_OOF.md`

## 3. Stage-3 implication / next leverage

Under experimental gates, saturated layers now include:

1. Portfolio-rule cluster (C2/C4/C8)
2. TECH2/PRICE8 × GLOBAL/BREADTH × λ
3. Existing family-score recombinations × several breadth/vol regime cuts

Next meaningful research needs **features beyond current family scores** and/or a **regime that actually partitions OOF differently and still clears dual gates** — still OOF-selected; one held-out pass only after a non-degenerate lock.

Do not promote 2.5% / 0.70. Do not merge PR #19 yet.
