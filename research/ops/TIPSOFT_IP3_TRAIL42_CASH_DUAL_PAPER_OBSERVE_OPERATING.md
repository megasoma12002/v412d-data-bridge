# TIPSOFT_P3_TRAIL42_FT_CASH dual-paper observe — OPERATING

- human_mdd: `Trail42 cash的mdd可接受` → sealed MDD **ACCEPTABLE**
- human_open: `OPEN paper observe: TIPSOFT_P3_TRAIL42_FT_CASH / (tip Soft Exact T+1 · Path3 ON when trail42d prem_p3≥−0.01 · /  Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · sealed MDD −0.36 ACCEPTABLE · /  NOT Soft-refill · NOT hybrid T+0)`
- status: **OPERATING_OBSERVE** · live_wire: false · apply/cutover: **BLOCKED** · Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · hybrid T+0 carve FORBIDDEN
- books: `L4_LIVE_P3_WITHIN` ∥ `TRAIL42_FT_CASH` (Exact T+1 tip Soft twin)
- gate: Path3 ON when trail42d prem_p3≥−0.01 · OFF→FIN∪TEL→cash
- held-out: CAGR↑ 1.4549 pp · MDD↑ 0.026 pp
- sealed: CAGR↑ 2.0026 pp · MDD↑ -0.3632 pp (**ACCEPTABLE**)
- tip ytd CAGR↑ 11.3364 · tip 1y CAGR↑ 10.4582

## Non-actions

- Soft-Frozen KEEP
- Soft FIN/TEL Exact T+1 stay OFF (Path3 WITHIN intent KEEP)
- Path4 live OFF
- hybrid Soft-core T+0 carve FORBIDDEN
- year-cut / lookahead promote FORBIDDEN
- Return-blend apply on tip order_rows FORBIDDEN
- Live −P3T0 apply / cutover BLOCKED until dedicated ACCEPT
- ON_UNLESS_MUTE_FT_CASH observe KEEP OPERATING (sibling 0kba)
- broker false

Repro: `repro/tipsoft-ip3-trail42-cash-paper-observe/`
