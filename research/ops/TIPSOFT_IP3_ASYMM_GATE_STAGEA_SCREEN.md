# TIPSOFT_IP3_ASYMM_GATE_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`IP3_ASYMM_YEAR_SOFT`** · champion=**`ASYMM_NEAR__X_R5NEG__MS8_CD3__P4_SAT`**
Register: **0kb0** · screened_mech=456 · held_pos=0 · year_gap_close=30

## Year-oracle baseline

- live gap_to_oracle **1.1068** pp · NEAR **0.7507** · P34 **0.738**
- base_best counts (live/P3/P3+P4): `{'live': 8, 'P3': 5, 'P3+P4': 2, 'policy': 6}`

## Family summary

| Family | n | held+ | gap_close | max heldΔNEAR | max gap↑ |
|---|---:|---:|---:|---:|---:|
| ASYMM | 228 | 0 | 18 | -0.024 | 0.5089 |
| ASYMM_MUTEX | 126 | 0 | 10 | -0.4397 | 0.2468 |
| HYST | 24 | 0 | 2 | -0.3347 | 0.0588 |
| MUTEX | 12 | 0 | 0 | -0.2714 | -0.0937 |
| SOFT | 24 | 0 | 0 | -0.0875 | -0.0024 |
| SOFT_ASYMM | 42 | 0 | 0 | -0.9028 | -0.157 |

## Top causal mechanism arms

| Arm | fam | heldΔNEAR | gap↑vsNEAR | sealedΔlive | tipYΔlive | vs live | ᾱ | p3% | p4% |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| ASYMM_NEAR__X_R5NEG__MS8_CD3__P4_SAT | ASYMM | -0.0759 | 0.3512 | -0.0523 | 6.9625 | HIT | 0.5466 | 54.66 | 21.09 |
| ASYMM_NEAR__X_R5NEG__MS8_CD3__P4OFF | ASYMM | -0.1012 | 0.3392 | -0.0434 | 6.6339 | HIT | 0.5466 | 54.66 | 0.0 |
| ASYMM_NEAR__X_R5NEG__MS5_CD3__P4_SAT | ASYMM | -0.1613 | 0.5089 | -0.0523 | 5.6764 | HIT | 0.4846 | 48.46 | 19.7 |
| ASYMM_NEAR__X_R5NEG__MS5_CD3__P4OFF | ASYMM | -0.1822 | 0.5003 | -0.0434 | 5.4217 | HIT | 0.4846 | 48.46 | 0.0 |
| ASYMM_NEAR__X_R5NEG__MS5_CD5__P4_SAT | ASYMM | -0.2879 | 0.2898 | -0.0523 | 6.0418 | HIT | 0.4284 | 42.84 | 17.05 |
| ASYMM_NEAR__X_R5NEG__MS0_CD0__P4_SAT | ASYMM | -0.2913 | 0.2464 | -0.0523 | 6.0486 | HIT | 0.4866 | 48.66 | 20.74 |
| ASYMM_NEAR__X_R5NEG__MS5_CD5__P4OFF | ASYMM | -0.3069 | 0.2809 | -0.0434 | 5.8054 | HIT | 0.4284 | 42.84 | 0.0 |
| ASYMM_NEAR__X_R5NEG__MS0_CD0__P4OFF | ASYMM | -0.3192 | 0.2328 | -0.0434 | 5.7018 | HIT | 0.4866 | 48.66 | 0.0 |
| ASYMM_NEAR__X_OFFPEAK5__MS8_CD3__P4_SAT | ASYMM | -0.3347 | 0.0588 | -0.0523 | 3.6497 | HIT | 0.7772 | 77.72 | 27.69 |
| HYST_PEAK3IN_PEAK5OUT_MS8_CD3__P4_SAT | HYST | -0.3347 | 0.0588 | -0.0523 | 3.6497 | HIT | 0.7772 | 77.72 | 27.69 |
| HYST_PEAK3IN_PEAK5OUT_MS8_CD5__P4_SAT | HYST | -0.3423 | 0.0548 | -0.0523 | 3.6497 | HIT | 0.7736 | 77.36 | 27.69 |
| ASYMM_NEAR__X_R5NEG__MS3_CD5__P4_SAT | ASYMM | -0.3917 | 0.4377 | -0.0523 | 6.0079 | HIT | 0.3818 | 38.18 | 15.45 |
| ASYMM_NEAR__X_R5NEG__MS3_CD5__P4OFF | ASYMM | -0.4068 | 0.4316 | -0.0434 | 5.8319 | HIT | 0.3818 | 38.18 | 0.0 |
| ASYMM_NEAR__X_R5NEG__MS3_CD3__P4_SAT | ASYMM | -0.5179 | 0.2733 | -0.0523 | 5.7882 | HIT | 0.4504 | 45.04 | 18.48 |
| ASYMM_NEAR__X_R5NEG__MS3_CD3__P4OFF | ASYMM | -0.5388 | 0.2637 | -0.0434 | 5.5434 | HIT | 0.4504 | 45.04 | 0.0 |
| ASYMM_NEAR_RISKON__X_R5NEG__MS0_CD0__MUTEXDEF__P4_SAT | ASYMM_MUTEX | -0.549 | 0.1327 | -0.0523 | 4.758 | HIT | 0.4043 | 40.43 | 18.81 |
| ASYMM_NEAR__X_R5NEG__MS0_CD0__MUTEXDEF__P4_SAT | ASYMM_MUTEX | -0.5514 | 0.132 | -0.0523 | 4.758 | HIT | 0.407 | 40.7 | 18.81 |
| ASYMM_NEAR_RISKON__X_R5NEG__MS0_CD0__MUTEXDEF__P4OFF | ASYMM_MUTEX | -0.5722 | 0.1218 | -0.0434 | 4.4822 | HIT | 0.4043 | 40.43 | 0.0 |
| ASYMM_NEAR__X_R5NEG__MS0_CD0__MUTEXDEF__P4OFF | ASYMM_MUTEX | -0.5747 | 0.1212 | -0.0434 | 4.4822 | HIT | 0.407 | 40.7 | 0.0 |
| ASYMM_NEAR_RISKON__X_R5NEG__MS5_CD3__MUTEXDEF__P4_SAT | ASYMM_MUTEX | -0.6817 | 0.2468 | -0.0523 | 4.0061 | HIT | 0.4052 | 40.52 | 17.86 |

## Oracle DIAG (lookahead)

| ORACLE_POS_DIAG__P4_SAT | heldΔNEAR 6.7378 | gap↑ 6.284 | sealed 0.2229 | tipY 14.6189 |

## Optimize / disposition

1. Objective: asymmetric enter≠exit / hysteresis / soft-α / COOL-mutex gates so daily stack select closes year-oracle gap without year dummies; held ≥ NEARPEAK3
2. Champion `ASYMM_NEAR__X_R5NEG__MS8_CD3__P4_SAT` fam=ASYMM held_vs_near=-0.0759 gap_improve=0.3512 sealed_vs_live=-0.0523 tipY=6.9625 live=HIT
3. Mechanism held_pos clears: n=0 · year_gap_close n=30 / screened_mech=456
4. By family: ASYMM:held+=0/gap=18/maxΔ=-0.024; ASYMM_MUTEX:held+=0/gap=10/maxΔ=-0.4397; HYST:held+=0/gap=2/maxΔ=-0.3347; MUTEX:held+=0/gap=0/maxΔ=-0.2714; SOFT:held+=0/gap=0/maxΔ=-0.0875; SOFT_ASYMM:held+=0/gap=0/maxΔ=-0.9028
5. NEAR year gap_to_oracle=0.7507 · live gap=1.1068 · P34 gap=0.738 · best_counts={'live': 8, 'P3': 5, 'P3+P4': 2, 'policy': 6}
6. Oracle DIAG best held_vs_near=6.7378 (lookahead — never promote)
7. Refs: REF_NEAR_HARD__P4OFF heldΔNEAR=-0.0; REF_NEAR_HARD__P4_SAT heldΔNEAR=0.0273; REF_NEAR_HARD__P4_ON_ALPHA heldΔNEAR=0.0273; REF_NEAR_SAT_HARD__P4OFF heldΔNEAR=-1.0134; REF_NEAR_SAT_HARD__P4_SAT heldΔNEAR=-0.9863; REF_NEAR_SAT_HARD__P4_ON_ALPHA heldΔNEAR=-0.9863
8. If IP3_ASYMM_HIT → draft observe; IP3_ASYMM_YEAR_SOFT → note only; IP3_ASYMM_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay only
9. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_asymm_gate_stagea.py`

Label: `TIPSOFT_IP3_ASYMM_GATE_STAGEA_SCREEN_2026-09-30__IP3_ASYMM_YEAR_SOFT`
