# Register #6 Sequential Ballots — One at a Time

Date: 2026-09-05  
Rule: **Do not bundle.** Finish / park item N before opening item N+1 live-facing work.  
Soft-Frozen: **[0.50, 0.95] KEEP**

| # | Topic | Pack | Status now |
|---|---|---|---|
| **1** | Odd-lot default → `E22_v2s_tw` | `ODD_LOT_PROMOTE_DECISION_PACK.md` | **ACTIVE** — par gate PASS (TWSE); awaiting human ballot |
| 2 | Tax / receivable formal books | `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` | **QUEUED** — not started |
| 3 | E45 live stitch | `E45_LIVE_STITCH_CHARTER.md` | **QUEUED** — not started |

## Item 1 — current ask (ACTIVE)

Par inventory (Soft-Frozen FIN + telecom): **VERIFIED NT$10** via TWSE `t187ap03_L` as-of 2026-09-04.  
`coverage_pass_for_promote = true` for promote-gate equities. 0050 ETF remains N/A.

**Future expansion reserved (does not change ballot):**  
`par_value_watchlist.csv` + `e22_par_value_inventory.py --add-codes … --fetch-twse`  
Expansion codes (`role=expand`) are stored for later universes; they are **not** promote blockers.  
Demo expand row: **2330** VERIFIED NT$10 (same TWSE source) — proves lookup path; remove anytime.

**Vote one (item 1 only):**

- `奇數股 ACCEPT promote` → dedicated DEFAULT flip PR (forward-only)
- `奇數股 ACCEPT research-only` → keep named books; default stays `E22_v2s`; park item 1 → start item 2
- `奇數股 REJECT` → document; park item 1 → start item 2

Items 2–3 stay untouched until item 1 is parked.

## Label

`REGISTER6_SEQUENTIAL_BALLOTS_2026-09-05`
