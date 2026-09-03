# V4.12-E50-A0 Point-in-Time Taiwan Equity Database

This package builds the survivorship-aware input database for E50-A.  It does
not select an alpha model and does not alter formal E16/E18/E22 trading.
PIT / no-survivorship contracts are HARD_FROZEN. This artifact version is a
SOFT_FROZEN data baseline under `FROZEN_GOVERNANCE.md`; rebuild only after a
reproducible defect, and never overwrite the prior baseline in place.

The all-market archive layer starts at the earliest available release date,
2004-02-11. The workflow discovers every `yearly_YYYY.zip` archive rather than
hard-coding a later start year.

## Data contract

- `security_master.csv`: current TWSE/TPEX ordinary-share master plus historical
  delisting records.
- `delistings.csv`: raw FinMind delisting observations.
- `trading_calendar.csv`: Taiwan trading calendar.
- `shards/raw/<code>.csv`: canonical unadjusted OHLCV and traded value.  This is
  the only layer allowed for T+1 execution prices.
- `shards/adjusted/<code>.csv`: research-only adjusted OHLCV for return and
  momentum features.
- `point_in_time_universe.csv`: daily eligibility flags and top-liquidity rank.
- `download_manifest.csv`: resumable per-security fetch status.
- `qc_status.json`: counts, limitations and SHA-256 hashes.

## Causal rules

1. A security becomes indicator-ready only after 252 observed sessions.
2. A security is excluded on and after its delisting date.
3. Price and 20-session liquidity filters use only data through that date.
4. The daily alpha universe contains at most the top 150 eligible names by
   trailing 20-session traded value.
5. Current constituents are never backfilled into old dates without history.
6. Adjusted prices may rank stocks but may never price an execution.

## Run

Smoke build:

```bash
python e50a0_build_point_in_time.py --out ../e50a0_smoke \
  --start 2015-01-01 --end 2026-08-31 \
  --codes 2330,2317,2454,2880,2412,2603,1301,2308
```

Resume a full current-master build:

```bash
python e50a0_build_point_in_time.py --out ../e50a0_data \
  --start 2004-02-11 --end 2026-08-31
```

For a genuinely complete historical universe, append every four-digit ordinary
share in `delistings.csv` to the fetch list as well.  The free API is per-name;
the shard layout makes long runs resumable.  A sponsor token may be passed with
`--token` but is never written to disk.

## Known boundary

FinMind's stock master is a current snapshot, not a historical industry master.
The builder retains delisted securities and uses first observed raw price as a
conservative listing proxy.  Historical industry reclassification is therefore
not yet safe for an industry-neutral alpha score and belongs in E50-A1.
