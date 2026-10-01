# TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`IP3_TRAIL_MUTE_HIT`** · champion=**`MUTE_P3_W63_Tm001__S3_MUTESAT`**
Register: **0kb1** · mech=468 · strong=9 · held_pos=11 · year_obj=14 · year_soft=21

## Live-win episode census (DIAG)

- live-win years: `[2012, 2013, 2014, 2015, 2016, 2019, 2020, 2025]`
- P3-win years: `[2017, 2018, 2022, 2023, 2024]` · P3+P4: `[2021, 2026]`
- drag episodes in live-win years: **258**
- drag feat (live-win): `{'n_days': 440, 'pct_sat_lead': 59.32, 'pct_risk_on': 85.91, 'mean_dd63': -0.0095, 'mean_trail_abs': 0.0165, 'mean_prem_p3': -10.4016, 'sum_prem_p3_pp': -45.7671}`
- help feat (P3-win): `{'n_days': 349, 'pct_sat_lead': 28.65, 'pct_risk_on': 77.08, 'mean_dd63': -0.0097, 'mean_trail_abs': 0.0161, 'mean_prem_p3': 10.805, 'sum_prem_p3_pp': 37.7095}`

## Year-oracle baseline

- NEAR gap **0.7507** · wins **6/15** · `{'live': 8, 'P3': 5, 'P3+P4': 2}`
- live gap **1.1068** wins **8** · P34 gap **0.738** wins **4**

## Family summary

| Family | n | strong | year_obj | year_soft | held+ | max heldΔ | max regret↑ | max winsΔ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MUTE_BIN | 108 | 0 | 0 | 3 | 0 | -0.0528 | 0.1113 | 0 |
| MUTE_CONF | 9 | 0 | 0 | 0 | 0 | -0.2439 | 0.2231 | -1 |
| MUTE_RISKON | 9 | 0 | 0 | 0 | 0 | -0.3809 | 0.0303 | -1 |
| MUTE_S3 | 162 | 0 | 0 | 6 | 0 | -0.052 | 0.1148 | 1 |
| MUTE_S3_MUTEX | 18 | 0 | 0 | 0 | 0 | -0.3906 | 0.0303 | -1 |
| MUTE_S3_SAT | 54 | 9 | 13 | 12 | 11 | 0.0704 | 0.2324 | 0 |
| MUTE_SOFT | 108 | 0 | 1 | 0 | 0 | -0.0125 | 0.0621 | 0 |

## Top arms

| Arm | fam | heldΔNEAR | regret↑ | winsΔ | wins | sealed | tipY | vs live | p3% | p4% |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| MUTE_P3_W63_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0704 | 0.1355 | 0 | 6 | -0.0523 | 6.0402 | HIT | 47.36 | 21.18 |
| MUTE_P3ON_W50_T00__S3_MUTESAT | MUTE_S3_SAT | 0.0297 | 0.2125 | -2 | 4 | -0.0523 | 5.4316 | HIT | 38.5 | 12.33 |
| MUTE_P3ON_W42_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0278 | 0.1933 | -2 | 4 | -0.0523 | 6.0402 | HIT | 48.51 | 22.34 |
| MUTE_P3ON_W50_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0501 | 0.1621 | -2 | 4 | -0.0523 | 6.0395 | HIT | 48.13 | 21.95 |
| MUTE_P3ON_W63_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0087 | 0.1279 | -2 | 4 | -0.0523 | 6.0402 | HIT | 47.45 | 21.27 |
| MUTE_P3_W10_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0273 | 0.105 | -2 | 4 | -0.0523 | 6.0402 | HIT | 50.51 | 24.33 |
| MUTE_P3ON_W21_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0273 | 0.0776 | -2 | 4 | -0.0523 | 6.0402 | HIT | 49.85 | 23.68 |
| MUTE_P3ON_W10_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0273 | 0.0655 | -2 | 4 | -0.0523 | 6.0402 | HIT | 50.65 | 24.48 |
| MUTE_P3ON_W5_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0273 | 0.0539 | -2 | 4 | -0.0523 | 6.0402 | HIT | 50.8 | 24.63 |
| MUTE_P3_W5_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0273 | 0.0152 | -2 | 4 | -0.0523 | 6.0402 | HIT | 50.74 | 24.57 |
| MUTE_P3_W21_Tm001__S3_MUTESAT | MUTE_S3_SAT | 0.0058 | 0.0084 | -3 | 3 | -0.0523 | 5.7388 | HIT | 49.64 | 23.47 |
| MUTE_P3_W42_Tm001__S3_MUTESAT | MUTE_S3_SAT | -0.0306 | 0.1038 | -1 | 5 | -0.0595 | 6.0402 | HIT | 47.98 | 21.81 |
| MUTE_P3_W42_Tm001__SOFT05_P4SAT | MUTE_SOFT | -0.0125 | 0.0621 | -1 | 5 | -0.0523 | 6.0402 | HIT | 50.83 | 24.66 |
| MUTE_P3ON_W42_T00__S3_MUTESAT | MUTE_S3_SAT | -0.0398 | 0.1992 | -3 | 3 | -0.0523 | 5.6475 | HIT | 38.71 | 12.54 |
| MUTE_P3ON_W50_Tm00005__S3_MUTESAT | MUTE_S3_SAT | -0.0295 | 0.1923 | -3 | 3 | -0.0523 | 5.8499 | HIT | 39.22 | 13.04 |
| MUTE_P3ON_W42_Tm0005__S3_MUTESAT | MUTE_S3_SAT | -0.0483 | 0.0981 | -5 | 1 | -0.0523 | 5.9406 | HIT | 46.23 | 20.05 |
| MUTE_P3_W63_Tm001__S3_P4T00 | MUTE_S3 | -0.1269 | 0.0608 | 1 | 7 | -0.0523 | 5.3414 | HIT | 46.49 | 13.22 |
| MUTE_P3_W42_Tm001__S3_P4T00 | MUTE_S3 | -0.052 | 0.1148 | -1 | 5 | -0.0524 | 6.0434 | HIT | 47.18 | 14.29 |
| MUTE_P3_W42_Tm001__S3_P4Tm0001 | MUTE_S3 | -0.0527 | 0.1114 | -1 | 5 | -0.0577 | 6.0402 | HIT | 47.18 | 21.66 |
| MUTE_P3_W42_Tm001__S3_P4Tm0005 | MUTE_S3 | -0.0528 | 0.1113 | -1 | 5 | -0.0595 | 6.0402 | HIT | 47.18 | 21.81 |

## Oracle DIAG

| ORACLE_MUTE_NEG_DIAG | heldΔNEAR 6.7501 | regret↑ 6.2992 | winsΔ 9 |

## Optimize / disposition

1. Objective: trailing prem mute + 3-state LIVE/P3/P3+P4 to raise year-wins / cut year-regret vs oracle; held ≥ NEAR−0.05; sealed/tip floors; no year-cut
2. Champion `MUTE_P3_W63_Tm001__S3_MUTESAT` fam=MUTE_S3_SAT held_vs_near=0.0704 regret↑=0.1355 winsΔ=0 wins=6 sealed=-0.0523 tipY=6.0402 live=HIT
3. Clears: strong=9 · held_pos=11 · year_obj=14 · year_soft=21 / mech=468
4. By family: MUTE_BIN:strong=0/year=0/soft=3/held+=0/maxΔ=-0.0528/winsΔ=0; MUTE_CONF:strong=0/year=0/soft=0/held+=0/maxΔ=-0.2439/winsΔ=-1; MUTE_RISKON:strong=0/year=0/soft=0/held+=0/maxΔ=-0.3809/winsΔ=-1; MUTE_S3:strong=0/year=0/soft=6/held+=0/maxΔ=-0.052/winsΔ=1; MUTE_S3_MUTEX:strong=0/year=0/soft=0/held+=0/maxΔ=-0.3906/winsΔ=-1; MUTE_S3_SAT:strong=9/year=13/soft=12/held+=11/maxΔ=0.0704/winsΔ=0; MUTE_SOFT:strong=0/year=1/soft=0/held+=0/maxΔ=-0.0125/winsΔ=0
5. NEAR gap=0.7507 wins=6/15 · live gap=1.1068 wins=8 · P34 gap=0.738 wins=4 · best_counts={'live': 8, 'P3': 5, 'P3+P4': 2}
6. Census live-win years=[2012, 2013, 2014, 2015, 2016, 2019, 2020, 2025] · drag_eps=258 · drag_feat={'n_days': 440, 'pct_sat_lead': 59.32, 'pct_risk_on': 85.91, 'mean_dd63': -0.0095, 'mean_trail_abs': 0.0165, 'mean_prem_p3': -10.4016, 'sum_prem_p3_pp': -45.7671}
7. Oracle DIAG held_vs_near=6.7501 (lookahead — never promote)
8. If IP3_TRAIL_MUTE_HIT → draft observe; IP3_TRAIL_YEAR_SOFT → note only; IP3_TRAIL_MUTE_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay
9. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail_prem_mute_stagea.py`

Label: `TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_SCREEN_2026-09-30__IP3_TRAIL_MUTE_HIT`
