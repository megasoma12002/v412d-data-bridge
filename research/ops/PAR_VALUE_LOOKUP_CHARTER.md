# Par-Value Lookup Charter — Odd-Lot CIL Dependency

Date: 2026-09-05  
Status: **CHARTER ACTIVE** — Soft-Frozen **[0.50, 0.95] KEEP**  
Promote-gate: Soft-Frozen FIN + telecom equities **VERIFIED** via TWSE (2026-09-04)  
Expansion: watchlist / `--add-codes` reserved for future equities (not promote blockers)

Authority: `ODD_LOT_PROMOTE_DECISION_PACK.md` · `TW_ODD_LOT_APPLY.md` · Gap #6.5 closeout  
Code: `scripts/e22_dividend_accounting.py` reads `data/corporate_actions/par_value_by_code.csv` (fallback provisional 10)

## Problem

Taiwan odd-lot cash-in-lieu is **面額 × 畸零股數**（算至元、元以下捨去）— **not** always NT$10.

- Many issuers still use **NT$10** par.  
- **彈性面額** issuers may use other pars (e.g. NT$1 / NT$5 / custom).  
- Par can **change over time** (`TaiwanStockParValueChange` / capital events).

Using a blind `par=10` for every code is a **data assumption**, not a verified fact.  
It is acceptable only as a **provisional default** while inventory is incomplete — **not** as a silent promote license.

## In scope

1. Build a **point-in-time par table** for Soft-Frozen / E22 books universe.  
2. Rank vendor sources; prefer official issuer / TWSE-TPEx / FinMind with as-of.  
3. Wire `E22_v2s_tw` to read per-code (and as-of) par — fail closed if missing when `require_par_table=True`.  
4. Add promote gate on odd-lot decision pack: inventory verified before DEFAULT flip.

## Out of scope / WON’T

- Soft-Frozen flip  
- Promote `E22_v2s_tw` in the same PR as this charter alone  
- Market-price CIL as formal substitute for unknown par  
- Rewrite `forward/e21` history when pars are corrected  
- Scrape Goodinfo / Wantgoo / CMoney as primary (blocked / unreliable)

## Soft-Frozen / E22 universe (promote-gate minimum)

Editable watchlist: `data/corporate_actions/par_value_watchlist.csv`

| Code | Role | Status (as-of 2026-09-04) |
|---|---|---|
| 2880 / 2886 / 2892 / 5880 | Soft-Frozen FIN sleeve | **VERIFIED NT$10** (TWSE) |
| 2412 / 3045 / 4904 | Telecom sleeve (E22 books) | **VERIFIED NT$10** (TWSE) |
| 0050 | ETF (stock-div path rare) | `ETF_RULES_LOOKUP_NEEDED` |
| TAIEX | Index | N/A |

### Future expansion (reserved)

Add codes **without** reopening the promote-gate set:

```bash
# Option A — edit watchlist (role=expand)
# Option B — CLI
python scripts/e22_par_value_inventory.py --add-codes 2330,2303 --fetch-twse
```

`role=expand` rows are looked up and stored for future books use; they **do not** block
`coverage_pass_for_promote`. Promote still keys only on Soft-Frozen FIN + telecom.

## Candidate sources (priority)

| Pri | Source | What it gives | Notes |
|---:|---|---|---|
| 1 | Issuer / 股務公告 + MOPS | Event-time par for that distribution | Gold for CIL on a specific ex |
| 2 | TWSE / TPEx issuer profile | Current listed par | Need history for PIT |
| 3 | FinMind `TaiwanStockInfo` | Static attributes if present | Confirm column exists per token tier |
| 4 | FinMind `TaiwanStockParValueChange` | Par change events | Build PIT from events + seed |
| 5 | Manual curated CSV | Fallback with citation URL + as-of | Required when APIs blank |

## Pass / fail

| Gate | Pass |
|---|---|
| Coverage | Every Soft-Frozen FIN + telecom code has par with `as_of` + `source` |
| Expansion | Extra codes may live as `role=expand`; **not** required for promote |
| PIT | Par used on stock-ex day = last known par ≤ that day (future: event table) |
| Default policy | Missing par → provisional 10 in research; promote mode requires VERIFIED gate |
| Evidence | `par_value_by_code.csv` + watchlist + repro inventory JSON/MD |
| Soft-Frozen | KEEP |

## Stage plan

```
A  Charter + provisional inventory CSV          DONE
B  TWSE openapi t187ap03_L verify (promote-gate) DONE
C  Manual cite fill for LOOKUP_NEEDED survivors  N/A (gate clear)
D  Wire e22_dividend_accounting to par table     DONE (load_par_value_table)
E  Odd-lot promote ballot (Item 1 only)          AWAITING HUMAN
F  Extensible per-code lookup (watchlist/CLI)    DONE — reserved for future equities
```

## Relation to odd-lot promote

| Ballot | Par table |
|---|---|
| ACCEPT promote now | Allowed iff `coverage_pass_for_promote=true` (promote-gate VERIFIED) |
| ACCEPT research-only | Historical option — superseded: live DEFAULT is now `E22_v2s_tw` (promoted 2026-09-05) |
| REJECT | N/A |

## Label

`PAR_VALUE_LOOKUP_CHARTER_2026-09-05`
