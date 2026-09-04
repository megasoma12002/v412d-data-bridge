# Stage-2 Alpha/Model OOF Screen

Portfolio rules fixed to **C4 wrapper**. Model axes only. OOF 2011–2018 only.

## Decision: `OOF_NO_NEW_MODEL_DUAL_GATE_WINNER`

TECH2 + BREADTH_REGIME is required for dual-gate under C4 wrapper; GLOBAL collapses bootstrap. PRICE8 + BREADTH has similar IC but fails OOF bootstrap (~0.51–0.53). Lambda is nearly inert for TECH2/BREADTH. No new feature/mode family clears both gates.

Baseline TECH2/BREADTH/λ=1.0: turnover=0.0205, bootstrap=0.8066, IC=0.1147

Best PRICE8: BREADTH_REGIME/λ=100.0 IC=0.1117 boot=0.5282 both=False

| feature | mode | λ | mean IC | turnover | bootstrap | both gates | CAGR | MDD |
|---|---|---:|---:|---:|---:|---|---:|---:|
| TECH2 | BREADTH_REGIME | 0.1 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| TECH2 | BREADTH_REGIME | 1.0 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| TECH2 | BREADTH_REGIME | 10.0 | 0.1147 | 2.05% | 0.8066 | True | 10.56% | -30.24% |
| TECH2 | BREADTH_REGIME | 100.0 | 0.1147 | 2.04% | 0.7928 | True | 10.33% | -30.88% |
| PRICE8 | BREADTH_REGIME | 100.0 | 0.1117 | 1.96% | 0.5282 | False | 7.63% | -29.89% |
| PRICE8 | BREADTH_REGIME | 10.0 | 0.1118 | 1.97% | 0.5150 | False | 7.55% | -30.49% |
| PRICE8 | BREADTH_REGIME | 1.0 | 0.1118 | 1.96% | 0.5100 | False | 7.46% | -31.65% |
| PRICE8 | BREADTH_REGIME | 0.1 | 0.1118 | 1.96% | 0.5100 | False | 7.46% | -31.65% |
| TECH2 | GLOBAL | 10.0 | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% |
| TECH2 | GLOBAL | 0.1 | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% |
| TECH2 | GLOBAL | 1.0 | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% |
| TECH2 | GLOBAL | 100.0 | 0.0604 | 0.60% | 0.1460 | False | 3.65% | -26.56% |
| PRICE8 | GLOBAL | 100.0 | 0.0649 | 1.58% | 0.1356 | False | 3.92% | -27.06% |
| PRICE8 | GLOBAL | 10.0 | 0.0648 | 1.54% | 0.1300 | False | 3.86% | -26.74% |
| PRICE8 | GLOBAL | 1.0 | 0.0648 | 1.54% | 0.1300 | False | 3.86% | -26.74% |
| PRICE8 | GLOBAL | 0.1 | 0.0648 | 1.54% | 0.1300 | False | 3.86% | -26.74% |

## Implication

Do not lock a lambda-only TECH2/BREADTH twin as M1. Keep C2/C4/C8 references. Next model stage needs features beyond TECH2/PRICE8 or a different regime definition, still selected on OOF only.

Artifacts: `reports/stage2_model_oof_summary.json`, `outputs/stage2_model_oof_grid.csv`
