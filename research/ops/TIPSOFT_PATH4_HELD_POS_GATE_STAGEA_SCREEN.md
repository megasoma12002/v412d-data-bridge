# TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`PATH4_HELD_POS_HIT`** · champion=**`P4_C001_NEAR&SAT`**
Register: **0kay** · screened=174 · held_pos_floor_clear=4 · held_pos_raw=4

## Top causal arms (ranked)

| Arm | heldΔNEAR | sealedΔlive | tipYΔlive | vs live | vs NEAR | p4% |
|---|---:|---:|---:|---|---|---:|
| P4_C001_NEAR&SAT | 0.0273 | -0.0523 | 6.0402 | HIT | SOFT | 24.66 |
| P4_C001_SAT_LEAD | 0.0254 | -0.0602 | 5.948 | HIT | SOFT | 34.88 |
| P4_C0005_NEAR&SAT | 0.0185 | -0.055 | 6.2573 | HIT | NO_EDGE | 24.66 |
| P4_C00025_DEFEND | 0.0085 | -0.0434 | 5.5945 | HIT | NO_EDGE | 21.57 |
| P4_C0005_SAT_LEAD | -0.0002 | -0.0641 | 6.1435 | HIT | NO_EDGE | 34.88 |
| P4_C0005_NEAR&DEFEND | -0.0073 | -0.0434 | 5.8863 | HIT | NO_EDGE | 9.06 |
| P4_C001_NEAR&R5NEG | -0.008 | -0.0434 | 5.7226 | HIT | NO_EDGE | 17.05 |
| P4_C00025_NEAR&SAT | -0.0089 | -0.054 | 5.7219 | HIT | NO_EDGE | 24.66 |
| P4_C001_LAG10_GT0.001 | -0.0117 | -0.0434 | 5.6789 | HIT | NO_EDGE | 5.97 |
| P4_C0005_NEAR&TRAIL02 | -0.0167 | -0.055 | 6.0926 | HIT | NO_EDGE | 15.18 |
| P4_C001_LAG10_GT0.0001 | -0.018 | -0.0417 | 5.8606 | HIT | NO_EDGE | 28.85 |
| P4_C001_NEAR&LAG10_GT1e-4 | -0.0217 | -0.0434 | 5.8265 | HIT | NO_EDGE | 12.54 |

## Oracle DIAG (lookahead)

| Arm | heldΔNEAR | sealedΔlive | tipYΔlive | vs live | vs NEAR | p4% |
|---|---:|---:|---:|---|---|---:|
| P4_C00025_ORACLE_POS_DIAG | 3.0158 | 0.0183 | 7.6875 | HIT | HIT | 48.4 |

## Optimize / disposition

1. Objective: Path4 gate with held_vs_NEARPEAK3 > 0 and live sealed/tip floors
2. Champion `P4_C001_NEAR&SAT` held_vs_near=0.0273 sealed_vs_live=-0.0523 tipY=6.0402 live=HIT near=SOFT
3. held_pos_vs_near clears floors: n=4 / screened=174
4. any held_vs_near>0 (ignoring floors): n=4
5. Oracle DIAG `P4_C00025_ORACLE_POS_DIAG` held_vs_near=3.0158 (lookahead — never promote)
6. If PATH4_HELD_POS_HIT → draft observe on top of 0kaw; else Path4 OFF KEEP
7. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_path4_held_pos_gate_stagea.py`

Label: `TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_SCREEN_2026-09-30__PATH4_HELD_POS_HIT`
