# Stage 6 Decision — STOP lend-fee 3A

Date: **2026-09-04**  
Feature set: `-z(lend_fee_1m)` monthly top-20% vs EW  
Source: FinMind `TaiwanStockSecuritiesLending` (new PIT; not fundamental YoY)

Artifacts: `repro/stage6-lend-fee-3a-20260904/`

## Result

| Gate | Outcome |
|---|---|
| Dev net40 mean excess | **−0.795%/mo** (fail) |
| Dev consec 3y neg / LOYO | fail gates → `dev_pass=false` |
| Sealed 2025+ net40 | +0.609%/mo (not used for retune) |

## Decision: `STOP_STAGE6_LEND_FEE_FEATURE_SET`

Do not retune fee transforms / universe after looking at sealed.  
Next 3A needs a **different** non-fundamental family (e.g. futures OI regime × sleeve timing, institutional flow) — not another lend-fee remix.
