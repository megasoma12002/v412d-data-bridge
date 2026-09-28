# FIN_SELL_QUALITY_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T05:33:48Z`
Status: **MDD_BLOCK** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · Exact T+1 **KEEP** · COOL **KEEP** · live wire **false**

Charter: `FIN_SELL_QUALITY_STAGEA_CHARTER.md`
Screen: `FIN_SELL_QUALITY_STAGEA_SCREEN.md`

## Verdict

**`MDD_BLOCK`**

CAGR sign: **chal − base** (buy-quality Stage A giveback labeling bug not repeated).

Hard `fin_sell_ok` overlays can lift held CAGR (best `S_NOT_BELOW_MA60` **+1.81pp**, `S_ABOVE_MA60` **+1.77pp**, `S_NOT_BELOW_MA120` **+1.15pp**) and often lift sell WR, but **all** legal books worsen held MDD beyond the −0.25pp floor (nearest still ≈ **−1.46pp** on `S_NOT_BELOW_MA120`). Tip-safe only on `S_NOT_BELOW_MA120` among CAGR-clear books.

No legal challenger cleared CAGR+MDD+tip jointly → **do not open observe** from Stage A.

## Binding

1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP
2. Even HIT → paper observe ballot only (separate ACCEPT for live)
3. Sell win-rate is diagnostic; not FIFO/tip rewrite
4. Sell loss-defer remains REJECTED
5. Default next: densify only if human opens Stage B with softer MDD charter — else STOP / DEFER

Label: `FIN_SELL_QUALITY_STAGEA_DECISION_PACK_2026-09-28__MDD_BLOCK__NO_LIVE`
