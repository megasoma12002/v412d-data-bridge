# FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_DRAFT

Date: 2026-09-28  
Status note: **SUPERSEDED 2026-09-28** by `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
Status (historical): **DRAFT — blocked on policy carve-out** · Soft-Frozen clips **KEEP** · live wire **false** · cutover **BLOCKED**

Depends on: `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_DRAFT.md` **ACCEPT** (or combined line B).

## Proposed human line (after / with carve-out)

```
OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · Exact T+0 carve-out T0_CARVE_FIN_SAT_SWITCH)
```

Or combined:

```
ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)
```

## Champion

- `P3_T0_STATE` — same-day `trail_rel_63 ≤ −0.01` → SAT else COMP（paper NAV switch）
- vs live: held CAGR↑ **+3.48** · tip YTD↑ **+2.73** · tip-clean · yearly **14–1**
- Alt: `P3_T0_ENTER_M1`（較弱 sealed／多年勝率）

## Non-goals

- Live wire / Soft-Frozen clip flip / live CONF α retune  
- Global Exact T+0 for other books  
- Expand feature／FFT／lag-1 grids

## Evidence

- `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md` (`T0_ONLY_EDGE`)
- `FIN_SAT_T1_LAG_PATH3_VS_BASE.md`
- Repro NAVs: `repro/fin-sat-t1-lag-path-compare-stagea/outputs/nav_P3_T0_STATE.csv`

Label: `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_DRAFT_2026-09-28__AWAITING_CARVEOUT`
