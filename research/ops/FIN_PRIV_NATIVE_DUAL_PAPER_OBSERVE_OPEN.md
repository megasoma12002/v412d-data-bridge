# 民營 Native Dual-Paper Observe — OPEN

Date: 2026-09-09  
Status: **OPERATING OBSERVE** (paper only)  
Human line: 民營習性 ≠ 公股 · native within-sleeve  
Soft-Frozen live **KEEP** · live wire **false**

## Books

| Book | Financial names | Within-sleeve |
|---|---|---|
| `PRIV_EQUAL` | PRIV_R3R4 | EQUAL |
| `PRIV_KD_MAY_Klt25_T15` | PRIV_R3R4 | `FIN_PRE_EXDIV_KD` season **May 1–31** · K&lt;25 · T−15 |

Soft-Frozen **sleeve weights** from live FINBAND (公股 features); Financial dollars → 民營 only.

## Why these two

- Stage A: `PRIV_KD_MAY_Klt25_T15` tip-clean · held-out **+0.63** vs EQUAL · sealed RO ~flat.  
- Matches Jun–Jul 民營 cash-ex better than 公股 Apr15–May15 transplant.  
- `PRIV_MIX_L75` held-out higher but sealed RO **−5.4** → not the primary observe pair.

## Gates (month-end)

Same tip gates as other observes: YTD / trailing 1y vs `PRIV_EQUAL` (ALERT 3pp / PAUSE 5pp).  
Held-out score is historical lock; tip is operating.

## Operating artifacts (wired)

| Artifact | Path |
|---|---|
| Dual-paper ledgers | `scripts/e16_fin_priv_native_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e16_fin_priv_native_month_end_monitor.py` |
| Observe operating memo | `research/ops/FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPERATING.md` |
| Month-end monitor output | `research/ops/FIN_PRIV_NATIVE_MONTH_END_MONITOR.{md,json}` |
| Repro root | `repro/fin-priv-native-dual-paper-observe/` |

As-of `2026-09-09`: month-end monitor alerts = **none**.

## WON’T

- Soft-Frozen flip · live e21 expand · auto-promote to live KD

## Artifacts

- Optimize: `FIN_PRIV_NATIVE_WITHIN_SLEEVE_OPTIMIZE.md`  
- Decision: `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md`  
- Repro: `repro/fin-priv-native-20260909/`  
- Runner: `scripts/e16_fin_priv_native_optimize.py`

## Label

`FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN_2026-09-09`
