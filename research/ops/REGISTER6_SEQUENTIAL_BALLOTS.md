# Register #6 Sequential Ballots — One at a Time

Date: 2026-09-05  
Rule: **Do not bundle.** Finish / park item N before opening item N+1 live-facing work.  
Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw`** (#73+#74 merged)

| # | Topic | Pack | Status now |
|---|---|---|---|
| 1 | Odd-lot default → `E22_v2s_tw` | `ODD_LOT_PROMOTE_DECISION_PACK.md` | **DONE** — ACCEPT promote; #73+#74 merged; DEFAULT live |
| **2** | Tax / receivable formal books | `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `TAX_RECEIVABLE_CHARTER_DECISION_PACK.md` | **ACTIVE** — awaiting human ballot |
| 3 | E45 live stitch | `E45_LIVE_STITCH_CHARTER.md` | **QUEUED** — untouched until Item 2 parked |

## Item 2 — current ask (ACTIVE)

Formal today: **`E22_v2s_tw` + TAX0 + cash on ex-date** (no receivable asset).  
This item opens a **charter ballot only** — no DEFAULT flip, no Soft-Frozen flip, no history rewrite.

**Vote one (item 2 only):**

- `稅應收 ACCEPT charter` → allow Stage B sandbox dual-books implementation (named `E22_v3_*`); default stays `E22_v2s_tw`
- `稅應收 DEFER charter` → park Item 2; keep TAX0 ex-date formal; then open Item 3
- `稅應收 REJECT` → close tax/receivable promote path this cycle; park Item 2; then open Item 3

Promote of any `E22_v3_*` to DEFAULT still needs a **second** human PR after sandbox evidence (not this ballot).

## Label

`REGISTER6_SEQUENTIAL_BALLOTS_2026-09-05__ITEM2_ACTIVE`
