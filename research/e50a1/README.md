# V4.12-E50-A1 Corporate Actions and Causal Fundamentals

E50-A1 extends the verified E50-A0 point-in-time equity universe. It does not
change E16, E18 or E22 and does not yet select an alpha model.

## Knowledge-date contract

- Quarterly statements use the statutory filing deadline and become usable on
  the next Taiwan trading day. The vendor period-end date is never a signal date.
- Monthly revenue uses the later of the statutory next-month day-10 deadline or
  a reliable post-2026-04-21 vendor `create_time`, then the next trading day.
- Dividend policy becomes usable on the trading day after announcement.
- Ex-date result rows are ex-post adjustment data only and cannot be used as a
  pre-event signal.
- Stock dividends, splits, reverse splits, par-value changes and capital
  reductions are normalized to `share_multiplier` per old share.
- EPS remains stored but is marked unsafe for direct cross-quarter addition
  when share counts changed. Alpha features should prefer income and a
  consistent share-count denominator.

## Full backfill

The current FinMind token permits per-stock fundamentals but not all-market
fundamental queries. `alpha_candidate_codes.txt` contains the 1,347 securities
that entered E50-A0's historical top-150 liquidity universe at least once.
Manual batches default to 80 codes; seven per-code datasets keep a batch below
the 600-request hourly allowance. Every raw dataset is stored by code so a
later run can resume without rewriting completed shards.

The first push run is a cross-industry causal-contract validation sample. A
complete total-return index is intentionally deferred until every corporate
action shard has been backfilled and reconciled.
