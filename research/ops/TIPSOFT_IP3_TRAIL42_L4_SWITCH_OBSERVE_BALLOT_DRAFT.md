# TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT

Date: 2026-10-01
Status: **DRAFT — awaiting human OPEN** · Soft KEEP · Soft FIN/TEL Exact T+1 stay **OFF** · Path4 live **OFF** · hybrid T+0 carve **FORBIDDEN** · tip apply / cutover **BLOCKED** until OPEN→OPERATING→ACCEPT

Register: **0kbd** · Parent Stage A `SIGNAL_SWITCH_HIT` · dual-book relative DD switch

## Proposed human line

```
OPEN paper observe: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH
(tip Soft Exact T+1 dual-book · daily TRAIL42 twin if TRAIL DD≥L4 DD else L4 ·
 Soft FIN/TEL stay OFF · NOT year-switch · NOT Path3-gate-only · NOT tip apply)
```

## Champion

- Challenger: `TRAIL42_L4_DD_SWITCH` = Stage A `SW_TRAIL_WHEN_TR_DD_GTE_L4`
- Base: `L4_LIVE_P3_WITHIN` (live tip twin)
- Rule: **daily** use TRAIL42×CASH tip Soft twin if TRAIL drawdown ≥ L4 drawdown, else L4
- Requires dual-book marking (L4∥TRAIL) — **not** Path3-gate-only · **not** year-switch
- vs L4: held **+3.5275** · tipY **+27.5471** · sealed MDD **0.4692**
- TRAIL days ~**57%** · Soft FIN/TEL stay OFF
- Sibling observes KEEP: 0kba MUTE×CASH · 0kbb TRAIL42×CASH

## Non-goals

- Calendar-year switch / year-oracle
- Path3-gate-only switch (no dual-book relative signal)
- Soft FIN/TEL Exact T+1 re-enable / WITHIN undo
- Research return-blend on tip order_rows
- Path4 live · broker · hybrid T+0
- Live tip apply / cutover without OPEN→OPERATING→ACCEPT
- Stamps-only LIVE_OVERRIDE substitute (different layer)

## Evidence

- `TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_DECISION_PACK.md` (0kbd)
- NAV: `repro/tipsoft-ip3-trail42-l4-signal-switch-stagea/outputs/nav_TRAIL_WHEN_TR_DD_GTE_L4.csv`
- Candidate: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_PAPER_OBSERVE_CANDIDATE.md`

Label: `TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT_2026-10-01__AWAITING_OPEN__NO_LIVE`
