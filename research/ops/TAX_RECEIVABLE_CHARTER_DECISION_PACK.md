# Tax / Receivable Formal Books — Charter Decision Pack (Item 2)

Date: 2026-09-05  
Status: **ACTIVE — AWAITING HUMAN BALLOT**  
Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw`** (TAX0; cash on ex-date; unchanged by this pack)

Authority: `HUMAN_DECISION_REGISTER.md` #6b · `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `REGISTER6_SEQUENTIAL_BALLOTS.md`

## Purpose

Give humans a single accept/defer/reject package for opening **sandbox** work on named formal books that model:

1. **Receivable / pay-date** cash clock (vs today’s ex-date credit)  
2. **Dividend withholding tax** (vs today’s TAX0)

This pack **does not** change `DEFAULT_BOOKS_VERSION`. Charter ACCEPT only unlocks Stage B sandbox PRs.

## Formal today (post Item 1)

| Topic | Live formal | Gap |
|---|---|---|
| Books version | `E22_v2s_tw` | Odd-lot par CIL already promoted |
| Cash dividend clock | Credit on **ex-date** | No receivable; cash early vs custody pay |
| Pay-date | In ledger fields; **not** cash clock | Ops liquidity timing not in NAV |
| Dividend / withholding tax | **TAX0** (pre-tax) | After-tax live books not named |
| Gap6 tax haircuts | Report-only | Must not silently become default |

## Proposed named versions (sandbox only until later promote)

| Version id | Rule sketch | Role |
|---|---|---|
| `E22_v2s_tw` | TW odd-lot; cash on ex; TAX0 | **Current formal default** |
| `E22_v3_recv_pay` | Receivable on ex; cash on pay-date; TAX0 | Timing-fidelity candidate |
| `E22_v3_tax10` / `tax20` | Ex-date cash × (1 − w); w∈{0.10,0.20} | After-tax sensitivity |
| `E22_v3_recv_pay_taxW` | Receivable + chosen withholding | Combined (only after each axis alone is clear) |

## Human ballot (Item 2 only)

| Ballot | Meaning | Next action |
|---|---|---|
| **ACCEPT charter** | Authorize Stage B sandbox dual-books under this charter | Open implementation PR(s); DEFAULT stays `E22_v2s_tw`; Soft-Frozen KEEP |
| **DEFER charter** | No implementation this cycle | Park Item 2; then open Item 3 (E45 stitch) |
| **REJECT** | Close tax/receivable promote path this cycle | Park Item 2 with reason; then open Item 3 |

Reply with one of:

- `稅應收 ACCEPT charter`
- `稅應收 DEFER charter`
- `稅應收 REJECT`

## Gates before any future DEFAULT promote (not this ballot)

| Gate | Required |
|---|---|
| Charter ACCEPT | This ballot |
| Sandbox evidence | Side-by-side NAV/CAGR/MDD vs `E22_v2s_tw` on sealed window |
| Tax rule written | One withholding assumption (resident/non-resident explicit) |
| Receivable identity | receivable + cash = ex-date credit; clears on pay |
| Dedicated promote PR | Second human ACCEPT; forward-only; Soft-Frozen KEEP |
| Forbidden bundle | Soft-Frozen flip, E45 stitch, history rewrite, odd-lot re-litigation |

## Explicit non-goals (this pack)

- Flip `DEFAULT_BOOKS_VERSION`  
- Soft-Frozen flip  
- Rewrite `forward/e21` history  
- In-place change of `E22_v2s_tw` semantics  
- E45 stitch (Item 3)  
- Auto-promote from Gap6 KPI prints  

## Label

`TAX_RECEIVABLE_CHARTER_DECISION_PACK_2026-09-05__AWAITING_HUMAN`
