# TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_EXECUTED_OPEN

Date: 2026-10-01
Status: **EXECUTED OPEN / OPERATING OBSERVE** · Soft KEEP · Soft FIN/TEL stay **OFF** · Path4 OFF · broker false · tip apply/cutover **BLOCKED**

Register: **0kbd** · Parent Stage A `SIGNAL_SWITCH_HIT` · supersedes `TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT`

## Human (exact)

```
OPEN paper observe: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH
(tip Soft Exact T+1 dual-book · daily TRAIL42 twin if TRAIL DD≥L4 DD else L4 ·
 Soft FIN/TEL stay OFF · NOT year-switch · NOT Path3-gate-only · NOT tip apply)
```

## What changed

| Item | Before | After OPEN |
|---|---|---|
| Observe ballot | DRAFT | **EXECUTED OPEN** |
| Dual-paper | candidate | **OPERATING** (`L4_LIVE_P3_WITHIN` ∥ `TRAIL42_L4_DD_SWITCH`) |
| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |
| Path4 / broker | OFF / false | **OFF / false** |
| Tip apply | — | **BLOCKED** (needs ACCEPT) |
| 0kba / 0kbb | OPERATING | **KEEP OPERATING** |

## Evidence

- held vs L4 **+3.5275** · tipY **+27.5471** · sealed MDD **0.4692**
- Operating: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPERATING.md`
- Stage A: `TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_DECISION_PACK.md`

## Non-actions

- Soft-Frozen KEEP
- Soft FIN/TEL Exact T+1 stay OFF
- Path4 live OFF
- Calendar-year switch / year-oracle FORBIDDEN
- Path3-gate-only switch (without dual-book relative signal) FORBIDDEN
- hybrid Soft-core T+0 carve FORBIDDEN
- Research return-blend on tip order_rows FORBIDDEN
- Live tip apply / cutover BLOCKED until dedicated ACCEPT
- Sibling 0kba MUTE×CASH observe KEEP OPERATING
- Sibling 0kbb TRAIL42×CASH observe KEEP OPERATING
- broker false

Label: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_EXECUTED_OPEN_2026-10-01__OPEN__NO_LIVE`
