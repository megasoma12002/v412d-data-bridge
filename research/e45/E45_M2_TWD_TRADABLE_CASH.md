# E45 M2 Tradable TWD Cash-like Twin Paper

- Generated: `2026-09-07T01:10:28.812162+00:00`
- Freeze: `research/e45/E45_M2_C35_TWDCASH_HIGHBETA_V0_FROZEN.md`
- Retail deposit NAV: **`UNAVAILABLE_FREE_FINMIND_TIER`**
- Listed proxies: `00740B`, `00751B`, equal-weight short basket
- Claim status: `RETIRED_HISTORICAL_NARRATIVE`

## §2 qualification

| Book | §2 | Held score | Giveback pp | MDD improve pp |
|---|---|---:|---:|---:|
| `M2_RELOC_BIL_FX_C50` | Y | +1.24 | +3.43 | +2.96 |
| `M2_RELOC_TWD_CASH_CBC_C50` | Y | +0.95 | +3.55 | +2.73 |
| `M2_RELOC_TWD_CASH0_C50` | Y | +0.80 | +3.80 | +2.70 |
| `M2_RELOC_TWD_720B_C50` | N | -3.62 | +4.31 | -1.47 |
| `M2_RELOC_TWD_740B_C50` | N | -3.01 | +4.15 | -0.94 |
| `M2_RELOC_TWD_740B_C75` | N | -3.66 | +6.39 | -0.46 |
| `M2_RELOC_TWD_751B_C50` | N | -2.81 | +4.57 | -0.52 |
| `M2_RELOC_TWD_751B_C75` | N | -3.40 | +7.01 | +0.11 |
| `M2_RELOC_TWD_SHORT_BASKET_C50` | N | -2.93 | +4.36 | -0.75 |
| `M2_RELOC_TWD_SHORT_BASKET_C75` | N | -3.55 | +6.71 | -0.20 |

**Challenger §2 PASS:** `none`
**Best challenger by giveback:** none

## Honesty

- `00740B` / `00751B` are **listed short-bond ETFs**, not bank deposits / MM funds.
- CBC rediscount remains a **policy** upper-bound carry proxy.
- Free FinMind cannot supply dated retail deposit-rate series for a true cash NAV.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN
- No observe OPEN / no C50 lock change from this paper
- No invent MDD replacement · no `live_market.csv` merge

## Reproduce

```bash
python3 scripts/e45_m2_twd_tradable_cash_paper.py
```

