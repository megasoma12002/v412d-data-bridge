# TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN

> **SUPERSEDED / OBSERVE CLOSED (2026-10-01)** — `TIPSOFT_P3_TRAIL42_FT_CASH` · twin leg absorbed into DD_SWITCH tip apply LIVE · `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md`

Date: 2026-10-01
Status: **OBSERVE CLOSED** · Soft KEEP · Soft FIN/TEL stay **OFF** · Path4 OFF · broker false · apply/cutover **BLOCKED**

Register: **0kbb** · Parent 0kba Stage B sensitivity · disposition `TIPSOFT_IP3_TRAIL42_CASH_SEALED_MDD_DISPOSITION` **ACCEPTABLE**

## Human (exact)

```
Trail42 cash的mdd可接受

OPEN paper observe: TIPSOFT_P3_TRAIL42_FT_CASH
(tip Soft Exact T+1 · Path3 ON when trail42d prem_p3≥−0.01 ·
 Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · sealed MDD −0.36 ACCEPTABLE ·
 NOT Soft-refill · NOT hybrid T+0)
```

## What changed

| Item | Before | After |
|---|---|---|
| Sealed MDD (−0.36pp) | `TWIN_MDD_BLOCK` | **ACCEPTABLE** |
| Observe | — | **EXECUTED OPEN** `TIPSOFT_P3_TRAIL42_FT_CASH` |
| Dual-paper | — | **OPERATING** (`L4_LIVE_P3_WITHIN` ∥ `TRAIL42_FT_CASH`) |
| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |
| Path4 / broker | OFF / false | **OFF / false** |
| 0kba ON_UNLESS_MUTE observe | OPERATING | **KEEP OPERATING** |
| Live −P3T0 apply | — | **BLOCKED** (needs ACCEPT) |

## Evidence

- held vs L4 **+1.4549** · tipY **+11.3364** · sealed MDD **-0.3632 ACCEPTABLE**
- Disposition: `TIPSOFT_IP3_TRAIL42_CASH_SEALED_MDD_DISPOSITION.md`
- Operating: `TIPSOFT_IP3_TRAIL42_CASH_DUAL_PAPER_OBSERVE_OPERATING.md`

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

Label: `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN_2026-10-01__OPEN__NO_LIVE`
