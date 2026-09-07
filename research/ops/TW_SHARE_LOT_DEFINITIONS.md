# Taiwan share-lot definitions (live + paper)

Human authority: 2026-09-07 — paper 亦改整張 1000；並定義一張／零股／畸零股。  
Soft-Frozen: **[0.50, 0.95] KEEP** · stitch **FORBIDDEN**

Canonical code: `scripts/tw_share_lots.py`

## Definitions

| Term | Meaning | Project handling |
|---|---|---|
| **一張** | **1000 股** (board lot / 整股 unit) | Live + paper order/fill sizing: multiples of 1000 only |
| **零股** | **1～999 股** | Not used for new orders in live/paper early-stack. May remain in holdings after stock-dividend integer floor until sold in 張 units |
| **畸零股** | **0.x 股** (&lt; 1 share) | **面額處理** via `E22_v2s_tw`: CIL = `floor(frac × par)` NTD (yuan truncate). Not traded as shares |

Do **not** conflate 零股 (1–999) with 畸零股 (0.x).

## Code defaults

- Live: `e21_forward_pipeline.BOARD_LOT` ← `tw_share_lots.BOARD_LOT` (=1000)
- Paper: `simulate_core(..., lot_size=BOARD_LOT)` default 1000; `e45_paper_harness.run_early_stack` same
- Sensitivity research may still pass `lot_size=1` explicitly (Gap6 legacy compare)
- Dividend 畸零股: `e22_dividend_accounting.tw_par_cil_cash` (par table or provisional NT$10)

## Related

- Live replay note: `LIVE_BOARD_LOT_1000_2026-09-07.md`
- Par lookup: `PAR_VALUE_LOOKUP_CHARTER.md`
- Promote pack: `ODD_LOT_PROMOTE_DECISION_PACK.md` (畸零股 CIL; trading lots now aligned separately)
