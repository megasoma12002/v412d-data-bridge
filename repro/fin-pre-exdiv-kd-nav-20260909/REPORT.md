# FIN_PRE_EXDIV_KD — paper NAV screen

Generated: `2026-09-09T00:31:44.381121+00:00`
Status: **PAPER_NAV_SCREEN** · Soft-Frozen **KEEP** · live wire **false**

## Rule

- Yahoo **K9/D9** · May15–Jun10 first **K<25** → soft-tilt accumulate
- Skip buy cash-ex **T−10…T0** (+ stock ex day)
- Capital **500M** · lot **1000** · Telecom=`TEL_EQUAL`

## vs `FIN_EQUAL`

| id | heldout score | MDD↑pp | CAGR giveback | YTD | 1y | tip-clean |
|---|---:|---:|---:|---|---|---|
| `FIN_EQUAL` | — | — | — | PASS | PASS | — |
| `FIN_RS_SOFT_TILT_EXDIV` | 0.530 | 1.112 | 1.163 | PAUSE_REVIEW | PAUSE_REVIEW | False |
| `FIN_PRE_EXDIV_KD` | 0.492 | 0.783 | 0.582 | ALERT | ALERT | False |
| `MIX_L75` | 0.127 | 0.303 | 0.351 | PASS | PASS | True |

## Primary detail (`FIN_PRE_EXDIV_KD`)

- Held-out score: **+0.492** (MDD↑ 0.783pp · CAGR giveback 0.582pp)
- Tip YTD giveback: 3.014895462762146 → **ALERT**
- Tip 1y giveback: 3.3105217395135167 → **ALERT**

## Verdict

FIN_PRE_EXDIV_KD held-out score +0.492 vs EQUAL; tip YTD=ALERT 1y=ALERT. Paper only — Soft-Frozen KEEP · no live wire.

## Hard rules

- Soft-Frozen KEEP · no live wire · no auto observe OPEN
- Event-study probe remains `FIN_PRE_EXDIV_KD_PROBE.md`

Repro: `repro/fin-pre-exdiv-kd-nav-20260909/`
