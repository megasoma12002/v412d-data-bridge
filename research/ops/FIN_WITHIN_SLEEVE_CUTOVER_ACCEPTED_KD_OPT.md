# FIN Within-Sleeve Live Cutover — ACCEPTED (KD_OPT)

Date: 2026-09-09  
Human ballot: **`ACCEPT`** (context: recommended `KD_OPT`; treated as  
`ACCEPT live FIN within-sleeve cutover: KD_OPT`)  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Soft-Frozen: **[0.50, 0.95] KEEP**  
DEFAULT books: **`E22_v2s_tw` KEEP**  
Live capital: **500M KEEP**  
Board-lot: **1000 KEEP**  
Telecom within-sleeve: **EQUAL KEEP**  
E45 stitch: **FORBIDDEN**

## Chosen policy

| Field | Value |
|---|---|
| Observe label | **`KD_OPT`** |
| Live `financial_alloc` | **`FIN_PRE_EXDIV_KD`** |
| Optimal id | **`KD_APR15_MAY15_Klt30_T15`** |
| Season | Apr15–May15 |
| Trigger | first Yahoo K9 &lt; 30 |
| Skip-buy | cash-ex T−15…T0 (+ stock ex day) |

## Gates at ACCEPT

| # | Gate | Pass? |
|---|---|---|
| 1–2 | Charter + OPERATING observe (4 books) | **YES** |
| 3 | Policy chosen = `KD_OPT` | **YES** |
| 4 | Tip YTD+1y PASS (~1.3 / 1.6 pp asof 2026-09-08) | **YES** |
| 5 | Held-out score ~+0.65 &gt; 0 | **YES** |
| 8 | Exact T+1 paper + live pipeline | **YES** |
| 9 | Live capital 500M | **YES** |
| 10–11 | Soft-Frozen / DEFAULT unchanged | **YES** |
| 13 | No Soft-Frozen / E45 / capital / books bundle | **YES** |

## Implementation

- `scripts/e21_forward_pipeline.py` — Financial sleeve orders via `allocate_sleeve_orders(FIN_PRE_EXDIV_KD)`  
- Telecom / 0050 remain equal-split  
- **Forward-only** — no `forward/e21` history wipe/replay  
- Existing EQUAL positions remain until rebalance gaps create KD_OPT-sized orders  

## Non-actions

- Soft-Frozen clip flip  
- E45 stitch  
- Telecom within-sleeve change  
- DEFAULT books flip  
- Capital change  
- History rewrite  

## Label

`FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_2026-09-09__KD_OPT__FORWARD_ONLY__SOFT_FROZEN_KEEP`
