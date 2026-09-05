# Par-Value Lookup Charter — Odd-Lot CIL Dependency

Date: 2026-09-05  
Status: **CHARTER OPEN (data research)** — Soft-Frozen **[0.50, 0.95] KEEP**  
Blocks: safe promote of `E22_v2s_tw` as live default until Soft-Frozen universe par table is verified

Authority: `ODD_LOT_PROMOTE_DECISION_PACK.md` · `TW_ODD_LOT_APPLY.md` · Gap #6.5 closeout  
Code today: `scripts/e22_dividend_accounting.py` hardcodes `PAR_VALUE_TWD = 10.0`

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

## Soft-Frozen / E22 universe (minimum)

| Code | Role | Provisional par (unverified) |
|---|---|---|
| 2880 / 2886 / 2892 / 5880 | Soft-Frozen FIN sleeve | 10.0 **LOOKUP_NEEDED** |
| 2412 / 3045 / 4904 | Telecom sleeve (E22 books) | 10.0 **LOOKUP_NEEDED** |
| 0050 | ETF (stock-div path rare) | N/A or ETF rules — **LOOKUP_NEEDED** |
| TAIEX | Index | N/A |

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
| PIT | Par used on stock-ex day = last known par ≤ that day |
| Default policy | Missing par → **fail closed** in promote mode; research mode may fall back to 10 with flag |
| Evidence | `data/corporate_actions/par_value_by_code.csv` + repro inventory JSON/MD |
| Soft-Frozen | KEEP |

## Stage plan

```
A  Charter + provisional inventory CSV (this change)
B  Vendor probe (FinMind Info / ParValueChange) when token available
C  Manual cite fill for any LOOKUP_NEEDED survivors
D  Wire e22_dividend_accounting to par table (opt-in flag)
E  Odd-lot promote ballot may ACCEPT only after D + coverage PASS
```

## Relation to odd-lot promote

| Ballot | Par table |
|---|---|
| ACCEPT promote now | **Blocked** until Stage D coverage PASS (or human explicitly accepts provisional par=10 risk in writing) |
| ACCEPT research-only | OK — keep named `E22_v2s_tw` with provisional par=10 + flags |
| REJECT | N/A |

## Label

`PAR_VALUE_LOOKUP_CHARTER_2026-09-05`
