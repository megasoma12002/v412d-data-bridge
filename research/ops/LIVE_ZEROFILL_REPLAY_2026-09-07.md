# Live Zero-Fill History Replay — 2026-09-07

Human authority: **「請清掉後重跑正確數據」**  
Soft-Frozen: **[0.50, 0.95] KEEP** · stitch **FORBIDDEN**

## Why

Code review P0: BUY-before-SELL depleted cash → **qty=0** `5880` BUY fills burned `order_id` (4 sessions). Forward-only code fix shipped in #113; historical rows were left intact until this explicit rewrite.

## What we did

1. Added `e21_forward_pipeline.py --asof` for controlled day replay.
2. Added `scripts/e21_replay_forward_ledger.py --confirm-history-rewrite`.
3. Cleared live books under `forward/e21/` (kept `live_market.csv`).
4. Replayed **11** complete sessions `2026-08-24` → `2026-09-07` with SELL-before-BUY.
5. Removed QC `LEGACY_ZERO_QTY_FILL_IDS` allowlist (no longer needed).
6. Orders now persisted SELL-before-BUY as well.

Authority artifact: `forward/e21/REPLAY_AUTHORITY.json`

## Results

| Check | Before (faulty) | After replay |
|---|---|---|
| qty≤0 fills | **4** | **0** |
| `2026-09-01-5880-BUY` fill qty | 0 | **716** |
| tip NAV (`2026-09-07`) | ≈ 3,207,833 | ≈ **3,209,457** |
| tip `5880` shares | 22,848 | **25,164** |
| `e21_qc` | PASS (with legacy allowlist) | **PASS** (no allowlist) |
| Gap6 | PASS | **PASS** |

## Non-actions

- Soft-Frozen / DEFAULT unchanged
- No stitch / cutover
- Market panel (`live_market.csv`) not regenerated (same prices)

Label: `LIVE_ZEROFILL_REPLAY_2026-09-07__AUTHORIZED_REWRITE__QC_GAP6_PASS`
