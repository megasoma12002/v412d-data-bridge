# TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN

> **SUPERSEDED / OBSERVE CLOSED (2026-10-01)** — `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` · superseded by DD_SWITCH tip apply LIVE (KEEPBOTH already NO) · `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md`

Date: 2026-10-01
Status: **OBSERVE CLOSED** · Soft KEEP · Soft FIN/TEL stay **OFF** · Path4 OFF · broker false · apply/cutover **BLOCKED**

Register: **0kba** · Parent Stage B `TWIN_HIT` · supersedes `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_DRAFT`

## Human (exact)

```
OPEN paper observe: TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH
(tip Soft Exact T+1 · Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead ·
 Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · NOT Soft-refill · NOT hybrid T+0)
```

## What changed

| Item | Before | After OPEN |
|---|---|---|
| Observe ballot | DRAFT | **EXECUTED OPEN** |
| Dual-paper | — | **OPERATING** (`L4_LIVE_P3_WITHIN` ∥ `ON_UNLESS_MUTE_FT_CASH`) |
| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |
| Path4 / broker | OFF / false | **OFF / false** |
| Live −P3T0 apply | — | **BLOCKED** (needs ACCEPT) |

## Evidence

- held vs L4 **+0.8735** · tipY **+2.4396** · sealed MDD **0.0173**
- Operating: `TIPSOFT_IP3_HIGHON_CASH_DUAL_PAPER_OBSERVE_OPERATING.md`
- Stage B: `TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md`

## Non-actions

- Soft-Frozen KEEP
- Soft FIN/TEL Exact T+1 stay OFF (Path3 WITHIN intent KEEP)
- Path4 live OFF
- hybrid Soft-core T+0 carve FORBIDDEN
- year-cut / lookahead promote FORBIDDEN
- Return-blend apply on tip order_rows FORBIDDEN
- Live −P3T0 apply / cutover BLOCKED until dedicated ACCEPT
- broker false

Label: `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN_2026-10-01__OPEN__NO_LIVE`
