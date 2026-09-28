# FIN×SAT Path3 P3_T0_STATE — Ballot EXECUTED (OPEN observe)

Date: 2026-09-28  
Status: **EXECUTED** · Soft-Frozen clips **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**  
Human (exact combined line B):

```
ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)
```

Policy parent: `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md` · carve-out **`T0_CARVE_FIN_SAT_SWITCH`**

## Evidence

- Stage A **`T0_ONLY_EDGE`** · champion `P3_T0_STATE` (same-day `trail_rel_63 ≤ −0.01` → SAT else COMP)
- Dual-paper first run: held CAGR↑ **+3.4758** · held MDD↑ **+0.0996** · tip YTD↑ **+2.7325** · tip 1y↑ **+1.7356** · %days SAT **24.16**
- Month-end asof 2026-09-24: sealed MDD alert (known −0.17pp) — observe only, not cutover
- Decision: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md` · `FIN_SAT_T1_LAG_PATH3_VS_BASE.md`
- Draft superseded: `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_DRAFT.md`

## Effect

- Dual-paper **OPERATING**: `CTRL_LIVE_A10` ∥ `P3_T0_STATE` under Exact T+0 carve-out
- Month-end + alert scan wired
- COMPOSITE `COMP_H150_x_A20` + `SAT_A20_RELAX` observes **KEEP OPEN** (parents parallel)
- Cutover **BLOCKED** · no live wire · do **not** expand T+0 carve-out

## Artifacts

- Operating: `FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING.md`
- Ledgers: `scripts/fin_sat_path3_t0_dual_paper_ledgers.py`
- Monitor: `scripts/fin_sat_path3_t0_month_end_monitor.py`
- Helpers: `scripts/fin_sat_path3_t0_observe_helpers.py`
- Repro: `repro/fin-sat-path3-t0-dual-paper-observe/`
- Cutover: `CUTOVER_CHECKLIST_FIN_SAT_PATH3_T0.md` (**BLOCKED**)

Label: `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_2026-09-28__OPEN__NO_LIVE`
