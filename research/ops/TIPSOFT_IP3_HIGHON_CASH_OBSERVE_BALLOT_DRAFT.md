# TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_DRAFT

Date: 2026-10-01  
Status: **DRAFT — awaiting human OPEN** · Soft KEEP · Soft FIN/TEL Exact T+1 stay **OFF** · Path4 live **OFF** · hybrid T+0 carve **FORBIDDEN** · cutover / apply **BLOCKED** until OPEN→OPERATING→ACCEPT

## Proposed human line

```
OPEN paper observe: TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH
(tip Soft Exact T+1 · Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead ·
 Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · NOT Soft-refill · NOT hybrid T+0)
```

## Champion

- Tip Soft twin: `TWIN_ON_UNLESS_MUTE_CASH`
- Soft-core parent: `ON_UNLESS_MUTE × FT_TO_CASH` (0kb9)
- Stitch: `tip_r = L4_r + (SC_fill − SC_WITHIN)`
- Soft FIN/TEL Exact T+1 stay OFF (no WITHIN loosen)
- Path3-ON ~**94.4%** · OFF ~**5.6%** → cash park FIN∪TEL
- vs L4: held **+0.8735** · tipY **+2.4396** · sealed MDD **+0.0173**
- 0kba Stage B **`TWIN_HIT`**
- Sensitivity `TRAIL42×CASH` twin: held **+1.45** tipY **+11.3** but sealed MDD **−0.36** → **MDD_BLOCK** (not observe champ)

## Non-goals

- Soft FIN/TEL Exact T+1 re-enable / WITHIN undo
- Research return-blend on tip `order_rows`
- Path4 live · broker · hybrid T+0 · year-cut
- Live −P3T0 apply without OPEN→ACCEPT

## Evidence

- `TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md`
- Parent: `TIPSOFT_IP3_UNLOCK_PATH_STAGEA_DECISION_PACK.md` (0kb9)
- Twin NAV: `repro/tipsoft-ip3-highon-cash-twin-stageb/outputs/nav_TWIN_ON_UNLESS_MUTE_CASH.csv`

Label: `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_DRAFT_2026-10-01__AWAITING_OPEN__NO_LIVE`
