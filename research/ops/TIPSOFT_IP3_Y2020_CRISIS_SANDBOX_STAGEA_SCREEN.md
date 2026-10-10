# TIPSOFT_IP3_Y2020_CRISIS_SANDBOX_STAGEA_SCREEN

Date: 2026-10-03 · Verdict: **`IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY`** · champion=**`MDD_D012_H018_S05`**
Register: **0kbg** · **SANDBOX_PARALLEL** · mech=28 · HIT=0 · SOFT=0 · MDD_ONLY=6 · HELD_BLOCK=0 · MDD_BLOCK=6

## Base

- `L4_LIVE_P3_WITHIN` path `repro/research-live-align-gap-stagea/outputs/nav_L4_LIVE_P3_WITHIN.csv`
- y2020 MDD **-0.14431069977736088** · Mar2020 MDD **-0.1300110855317218** (2020-02-20→2020-03-23)
- floors: held≥**0.1** · y2020 MDD↑≥**0.5** · Mar MDD↑≥**1.0** · sealed≥**-0.25**

## vs 0kb4

- Different mechanism family — 0kb4 failed held+∧y20 on residual stack knives; 0kbg screens synthetic crisis exposure on twin NAV. Neither unlocks soak freeze.

## Family summary

| Family | n | HIT | MDD help | held+ | max held | max y20 MDD↑ | max Mar MDD↑ | max sealed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| COMBO | 4 | 0 | 4 | 0 | -6.1458 | 4.3652 | 9.1784 | -0.6517 |
| MA200 | 2 | 0 | 2 | 0 | -4.5416 | 5.6809 | 8.5116 | -0.7476 |
| MDD | 6 | 0 | 6 | 0 | -0.2637 | 3.2625 | 3.3171 | 0.0 |
| VOL | 16 | 0 | 4 | 0 | -0.2927 | 1.6427 | 1.8257 | 0.9443 |

## Top arms

| Arm | fam | held | y2020 MDD↑ | Mar2020 MDD↑ | sealed | tipY | verdict |
|---|---|---:|---:|---:|---:|---:|---|
| MDD_D012_H018_S05 | MDD | -0.2637 | 1.0665 | 1.0843 | 0.0 | 0.0 | MDD_ONLY |
| MDD_D012_H018_S04 | MDD | -0.3178 | 1.2798 | 1.3012 | 0.0 | -0.0 | MDD_ONLY |
| MDD_D008_H012_S05 | MDD | -1.2455 | 2.7128 | 2.7582 | 0.0 | -0.0 | MDD_ONLY |
| MDD_D01_H015_S05 | MDD | -1.3238 | 1.8771 | 1.9085 | 0.0 | 0.0 | MDD_ONLY |
| MDD_D01_H015_S04 | MDD | -1.6696 | 2.2553 | 2.293 | 0.0 | 0.0 | MDD_ONLY |
| MDD_D008_H012_S04 | MDD | -2.5523 | 3.2625 | 3.3171 | 0.0 | 0.0 | MDD_ONLY |
| VOL_W20_T01_F04 | VOL | -2.9311 | 0.8223 | 1.6727 | 0.7704 | -16.5773 | TIP_BLOCK |
| VOL_W20_T01_F03 | VOL | -2.9324 | 0.8223 | 1.6727 | 0.7704 | -16.6956 | TIP_BLOCK |
| VOL_W63_T01_F03 | VOL | -3.0863 | 1.6427 | 1.8257 | 0.3612 | -20.267 | TIP_BLOCK |
| VOL_W63_T01_F04 | VOL | -3.0863 | 1.6427 | 1.8257 | 0.3612 | -20.267 | TIP_BLOCK |
| MA200_CASH025 | MA200 | -4.5416 | 5.6809 | 6.323 | -0.7476 | -12.4759 | MDD_BLOCK |
| MA200_CASH00 | MA200 | -6.0756 | 4.0634 | 8.5116 | -1.8139 | -16.4395 | MDD_BLOCK |
| COMBO_MA200_x_MDD10_15 | COMBO | -6.1458 | 4.0634 | 8.5116 | -1.8139 | -16.4395 | MDD_BLOCK |
| COMBO_MA200_x_VOL63_T014_F04 | COMBO | -6.572 | 4.3652 | 8.5116 | -1.8743 | -23.2279 | MDD_BLOCK |
| COMBO_VOL20_T012_F03_x_MA200 | COMBO | -7.1235 | 4.1108 | 9.1784 | -0.6517 | -25.4868 | MDD_BLOCK |
| COMBO_VOL_MA_x_MDD10_15 | COMBO | -7.193 | 4.1108 | 9.1784 | -0.6517 | -25.4868 | MDD_BLOCK |
| VOL_W63_T016_F03 | VOL | -0.2927 | 0.0 | 0.0 | 0.0 | -3.1816 | TIP_BLOCK |
| VOL_W63_T016_F04 | VOL | -0.2927 | 0.0 | 0.0 | 0.0 | -3.1816 | TIP_BLOCK |
| VOL_W63_T014_F03 | VOL | -0.8474 | 0.0 | 0.0 | 0.0 | -7.6184 | TIP_BLOCK |
| VOL_W63_T014_F04 | VOL | -0.8474 | 0.0 | 0.0 | 0.0 | -7.6184 | TIP_BLOCK |
| VOL_W20_T016_F03 | VOL | -0.9228 | -0.0246 | 0.0398 | 0.2611 | -5.9841 | TIP_BLOCK |
| VOL_W20_T016_F04 | VOL | -0.9228 | -0.0246 | 0.0398 | 0.2611 | -5.9841 | TIP_BLOCK |
| VOL_W20_T014_F03 | VOL | -1.2752 | 0.0048 | 0.3233 | 0.5081 | -7.6612 | TIP_BLOCK |
| VOL_W20_T014_F04 | VOL | -1.2752 | 0.0048 | 0.3233 | 0.5081 | -7.6612 | TIP_BLOCK |
| VOL_W63_T012_F03 | VOL | -1.7018 | 0.2218 | 0.2255 | 0.0309 | -14.0578 | TIP_BLOCK |

## Optimize / disposition

1. Objective: SANDBOX crisis overlays on L4 Path3 WITHIN NAV — cut Mar2020/y2020 MDD without held destroy
2. Champion `MDD_D012_H018_S05` fam=MDD held=-0.2637 y2020MDD↑=1.0665 Mar2020MDD↑=1.0843 sealed=0.0 tipY=0.0 verdict=MDD_ONLY
3. Clears: HIT=0 · SOFT=0 · MDD_ONLY=6 · HELD_BLOCK=0 · MDD_BLOCK=6 / mech=28
4. Base L4 y2020 MDD=-0.14431069977736088 · Mar2020 MDD=-0.1300110855317218
5. Compare 0kb4: Y2020_DEFEND_NO_EDGE (defend/FUSE knives) — different family; stop_freeze_0kb2 KEEP
6. Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · does **not** reopen 0kb2 residual stacks
7. Soft KEEP · Path4 OFF · broker false · no tip apply · no Soft FIN/TEL ACCEPT · no yearmix

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_sandbox_stagea.py`

Label: `TIPSOFT_IP3_Y2020_CRISIS_SANDBOX_STAGEA_SCREEN_2026-10-03__IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY__SANDBOX_PARALLEL`
