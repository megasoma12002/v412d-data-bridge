# TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH dual-paper observe — OPERATING

- human_open: `OPEN paper observe: TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH / (tip Soft Exact T+1 · Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · /  Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · NOT Soft-refill · NOT hybrid T+0)`
- status: **OPERATING_OBSERVE** · live_wire: false · apply/cutover: **BLOCKED** · Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · hybrid T+0 carve FORBIDDEN
- books: `L4_LIVE_P3_WITHIN` ∥ `ON_UNLESS_MUTE_FT_CASH` (Exact T+1 tip Soft twin)
- gate: Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · OFF→FIN∪TEL→cash
- held-out: CAGR↑ 0.8735 pp · MDD↑ 0.0654 pp
- sealed: CAGR↑ 0.5078 pp · MDD↑ 0.0173 pp
- tip ytd CAGR↑ 2.4396 · tip 1y CAGR↑ 1.5106

## Non-actions

- Soft-Frozen KEEP
- Soft FIN/TEL Exact T+1 stay OFF (Path3 WITHIN intent KEEP)
- Path4 live OFF
- hybrid Soft-core T+0 carve FORBIDDEN
- year-cut / lookahead promote FORBIDDEN
- Return-blend apply on tip order_rows FORBIDDEN
- Live −P3T0 apply / cutover BLOCKED until dedicated ACCEPT
- broker false

Repro: `repro/tipsoft-ip3-highon-cash-paper-observe/`
