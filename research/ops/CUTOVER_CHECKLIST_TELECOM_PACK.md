# Cutover Checklist — Telecom Within-Sleeve Pack

Date: 2026-09-09  
Status: **DRAFTED / NOT AUTHORIZED** — pack ballot OPEN; do **not** wire without ACCEPT  
Ballot: `TELECOM_PACK_CUTOVER_BALLOT_OPEN.md`  
Live today: Telecom **`TEL_EQUAL`** · FIN **`KD_OPT`** · Soft-Frozen FINBAND **[0.60, 0.90]**

## Gates

| # | Gate | Current | Pass? |
|---|---|---|---|
| 1 | Pack Stage C evidence on disk | `TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C.md` | **YES** |
| 2 | Re-screen under **live** FIN KD_OPT | `TELECOM_PACK_BALLOT_RESCREEN.md` | **YES** |
| 3 | Chosen pack held-out score **> 0** vs TEL_EQUAL under live stack | Best DIVERSIFY **−0.385** | **NO** |
| 4 | Tip YTD+1y PASS on chosen pack vs EQUAL | DIVERSIFY PASS/PASS | **YES** |
| 5 | Soft-Frozen unchanged in cutover PR | Policy | Policy |
| 6 | FIN KD_OPT unchanged | Policy | Policy |
| 7 | DEFAULT `E22_v2s_tw` KEEP | Policy | Policy |
| 8 | Forward-only; no history rewrite | Policy | Policy |
| 9 | Dedicated human ACCEPT string | Ballot OPEN | Pending |
| 10 | Not bundling Soft-Frozen / E45 / FIN / capital | Policy | Policy |

## Blocker now

Gate **3** fails under live FIN=`KD_OPT` re-screen. Recommend **`KEEP live TEL_EQUAL`**.

## Label

`CUTOVER_CHECKLIST_TELECOM_PACK_2026-09-09__NOT_AUTHORIZED__GATE3_FAIL`
