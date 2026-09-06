# E45 M2 — True DEF Data Ingest (research)

Generated: 2026-09-06  
Status: **INGEST DONE / PAPER JOIN NOT STARTED**  
Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN** · HIGH_BETA **DRAFT / NOT OPEN**

Freeze: `research/e45/E45_M2_TRUE_DEF_DATA_V0_FROZEN.md`  
Data: `data/def_proxies/` · QC: `data/def_proxies/qc_summary.json`  
Fetcher: `scripts/fetch_e45_true_def_proxies.py`

## Verdict: **INGEST PASS** (`overall_pass=true`)

| Series | Rows | Span | Role |
|---|---:|---|---|
| `00719B` | 2089 | 2018-02-01 → 2026-09-04 | Preferred TWD short-duration DEF |
| `00679B` / `00687B` | 2347 / 2294 | 2017+ | Long-duration stress only (not cash) |
| `BIL` / `SHY` | 4194 each | 2010-01-04 → 2026-09-04 | USD cash-like; need FX |
| `USDTWD` mid | 4138 | 2010-01-04 → 2026-09-04 | Research FX join |

## Read-through

1. Closes the M2 v0 honesty gap (“no cash/duration in live_market”) at the **research data** layer.
2. Does **not** replace `DEF_TEL` PASS; M2 v1 relocate paper still needs freeze + join + §2 rescreen.
3. Listing lag on `00719B` means early-stack pre-2018 must use an explicit policy (BIL_FX or cash@0) — freeze before metrics.
4. Parallel human path: M2 observe ballot for `M2_RELOC_TEL_C50` remains **DRAFT** until ACCEPT.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN
- No merge into `forward/e21/live_market.csv` in this pack
- Claimed MDD: `RETIRED_HISTORICAL_NARRATIVE`

## Reproduce

```bash
python3 scripts/fetch_e45_true_def_proxies.py
```
