# Telecom PRE_EXDIV_KD optimize (FIN-parallel)

Generated: `2026-09-09T13:39:45.660707+00:00`
Status: **STOP** — **0 coexist**
Soft-Frozen **[0.6, 0.9]** · FIN=`KD_OPT` · live wire **false** · capital **500,000,000**
Grid: seasons=['JUN', 'JUN15_JUL31', 'JUL', 'JUL15_AUG15', 'JUN_AUG', 'MAY15_AUG15'] · K=[20.0, 25.0, 30.0] · T=[5, 10, 15] · n=54

## Best (`max_heldout_only`)

- **`TEL_KD_MAY15_AUG15_Klt25_T10`** held-out **-0.376** · tip PASS/PASS · coexist=False
- season MAY15_AUG15 · K&lt;25.0 · T−10

Coexist count: **0** · no-PAUSE & score>0: **0**

## Top5 by held-out

| id | score | MDD↑ | CAGR gb | YTD | 1y | coexist |
|---|---:|---:|---:|---|---|---|
| `TEL_KD_MAY15_AUG15_Klt25_T10` | -0.376 | -0.201 | 0.351 | PASS | PASS | False |
| `TEL_KD_MAY15_AUG15_Klt20_T10` | -0.390 | -0.207 | 0.367 | PASS | PASS | False |
| `TEL_KD_JUN_Klt20_T10` | -0.391 | -0.207 | 0.369 | PASS | PASS | False |
| `TEL_KD_JUN_Klt25_T10` | -0.391 | -0.207 | 0.369 | PASS | PASS | False |
| `TEL_KD_JUN_AUG_Klt20_T10` | -0.391 | -0.207 | 0.369 | PASS | PASS | False |

## Hard rules

- Soft-Frozen / live e21 Telecom EQUAL untouched
- No live cutover from this grid

Repro: `repro/telecom-pre-exdiv-kd-optimize-20260909/`
