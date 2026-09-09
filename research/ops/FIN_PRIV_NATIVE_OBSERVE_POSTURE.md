# 民營 Native Observe Posture — LOCKED (paper observe)

Date: 2026-09-09  
Status: **LOCKED** · dual-paper **OPERATING OBSERVE** · live wire **false**  
Soft-Frozen: **[0.60, 0.90] LIVE** (FINBAND) · membership **公股 R1 KEEP**  
Live Financial within-sleeve: **公股 `KD_OPT` KEEP** · E45 stitch **OFF** (`DROP_E45_A05`)  
Open note: `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN.md` · decision: `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md`

## Binding hold

Human **「請全做」** (2026-09-09) — lock fixed month-end cadence + tip/structural watch + observe-status ballot (paper only).

1. **Maintain paper dual-book** — `PRIV_EQUAL` ∥ `PRIV_KD_MAY_Klt25_T15` @ 500M / lot 1000.  
2. **Month-end observe** — refresh ledgers + monitor; read tip (YTD/1y) + structural (held-out/sealed).  
3. **Default status** — **KEEP OBSERVE** while alerts empty and held-out score &gt; 0.  
4. **No live wire** — no e21 民營 expand · no Soft-Frozen 4-sleeve · no 公股 KD retune from this track.  
5. **Status ballot only** — escalate to stricter paper or STOP observe via ballot; never auto-promote.

## Posture (2 paper books · live untouched)

| Layer | Policy |
|---|---|
| Live Soft-Frozen / FIN names | FINBAND + **公股 R1** KEEP |
| Live Financial within-sleeve | **`KD_OPT`** (公股 calendar) KEEP |
| Paper observe | `PRIV_EQUAL` ∥ `PRIV_KD_MAY_Klt25_T15` |
| Status default | **KEEP OBSERVE** |

## Operating paths

| Role | Path |
|---|---|
| Pack | `scripts/ops_month_end_paper_pack.py` (`--refresh-ledgers` as needed) |
| Ledgers | `scripts/e16_fin_priv_native_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_fin_priv_native_month_end_monitor.py` |
| Checklist | `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST.md` |
| Runbook | `FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md` |
| Status ballot | `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md` |

## Tip / held-out reading guide

| Book / window | Expect |
|---|---|
| **`PRIV_KD_MAY_Klt25_T15` tip** | YTD+1y no ALERT/PAUSE (asof 2026-09-09: clean) |
| **Held-out** | Score ~**+0.63** vs `PRIV_EQUAL` |
| **Sealed** | ~flat (report-only) |

## Hard non-actions

- No Soft-Frozen flip / 4-sleeve Class D from this posture  
- No live e21 universe expand  
- No retune of native May KD params without new human OPEN  
- No conflating 民營 paper green with live 公股 KD promote  
- No history rewrite  

## Status ballot gate

| Path | Prerequisite |
|---|---|
| KEEP OBSERVE | Default; tip clean + held-out &gt; 0 |
| Stricter paper | Tip PAUSE ≥2 months **or** structural ALERT **or** human OPEN |
| STOP observe | Sustained tip fail **and** held-out collapse · archive ledgers |
| Live expand / 4-sleeve | **Out of scope** — new charter required |

## Label

`FIN_PRIV_NATIVE_OBSERVE_POSTURE_2026-09-09__KEEP_OBSERVE__NO_LIVE_WIRE`
