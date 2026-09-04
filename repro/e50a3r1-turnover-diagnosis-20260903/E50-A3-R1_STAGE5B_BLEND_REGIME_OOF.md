# Stage-5B Score Blend + Regime-Conditional OOF

C4 wrapper fixed. 2011–2018 OOF only. Follow-up to Stage-5A (no dual-gate winner).

## Decision: `OOF_NO_NEW_BLEND_REGIME_DUAL_GATE_WINNER`

| cell | IC | turn | boot | both | CAGR | MDD |
|---|---:|---:|---:|---|---:|---:|
| TECH2 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| BLEND_TECH2_30_DEF4_70 | 0.1160 | 1.78% | 0.6972 | False | 9.53% | -28.39% |
| BLEND_TECH2_70_DEF4_30 | 0.1182 | 1.80% | 0.6420 | False | 8.58% | -27.93% |
| REGIME_PICK_TECH2_ON_DEF4_OFF | 0.1211 | 1.89% | 0.6044 | False | 8.83% | -26.07% |
| REGIME_PICK_DEF4_ON_TECH2_OFF | 0.1041 | 1.68% | 0.5758 | False | 8.35% | -31.53% |
| BLEND_TECH2_50_DEF4_50 | 0.1179 | 1.72% | 0.5500 | False | 7.52% | -29.02% |
| REGIME_PICK_TECH2_ON_ORTHDEF_OFF | 0.1188 | 1.94% | 0.5390 | False | 7.83% | -28.60% |
| BLEND_TECH2_50_ORTHDEF_50 | 0.1288 | 1.71% | 0.4696 | False | 6.78% | -37.34% |

No new blend/regime-switch dual-gate winner.

Artifact: `reports/stage5b_blend_regime_oof_summary.json`
