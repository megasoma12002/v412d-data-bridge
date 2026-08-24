# V4.12-F Daily Forward Paper Trading System

Date deployed: 2026-08-24  
Status: **ACTIVE — first GitHub Actions run completed successfully**

## Objective

Accumulate genuinely new, post-freeze evidence for frozen V4.12-D and frozen E4 without further historical parameter tuning.

## Daily automation

- Schedule: weekdays at 16:30 Asia/Taipei (08:30 UTC).
- Manual trigger: supported through `workflow_dispatch`.
- Workflow: `.github/workflows/v412f-forward-paper.yml`.
- Concurrency lock prevents overlapping runs.
- GitHub contents write permission is limited to committing generated `forward/` records.
- Same-date reruns replace the D/E4 rows rather than duplicating them.

## Data pipeline

1. Download official-derived historical yearly/current weekly archives.
2. Rebuild canonical raw/unadjusted 12-stock OHLCV.
3. Supplement the most recent 14 calendar days from the official TWSE `MI_INDEX` endpoint.
4. Run raw-data QC.
5. Rebuild the separate corporate-action-adjusted evaluation layer through the current date.
6. Generate frozen D and E4 targets at close T for the next TWSE session open.
7. Commit the idempotent forward records and upload a 90-day workflow artifact.

## Frozen models

### V4.12-D benchmark

- family 1;
- top 2 per router;
- 21-trading-day selection cycle;
- 75-day Capital Lock;
- 80% Core + 20% monthly Tilt;
- R0 cash only for unused Tilt;
- T close signal, T+1 open execution.

### E4 forward challenger

- E3 continuous risk/volatility controller;
- 14% volatility target;
- maximum 50% exposure cut;
- 20-day slow recovery;
- 84-day minimum stock hold;
- challenger hurdle equal to 5× estimated round-trip cost;
- execute 25% of each new target-weight distance.

## First official forward snapshot

- Signal date: 2026-08-24.
- Canonical raw rows: 64,547.
- Adjusted evaluation rows: 64,547.
- D invested target: 96.17%; cash target: 3.83%.
- E4 risk exposure: 78.48%.
- E4 invested target: 75.27%; cash target: 24.73%.
- Execution instruction: target applies at the next TWSE session open.

The first formal workflow run was GitHub Actions run `32733980475`, conclusion `success`. Artifact `v412f-forward-paper-1` was created with artifact id `9522554665`.

## Persisted records

- `forward/latest_signal.json`: latest current and next-open weights.
- `forward/signals_history.csv`: one D and one E4 record per signal date.
- `forward/paper_nav_recomputed.csv`: adjusted evaluation curves from the frozen forward start.
- `forward/forward_qc.json`: source dates, row counts, model weight sums, and causal-rule checks.
- `forward/config.json`: frozen definitions and promotion rule.

## Interpretation and promotion rule

V4.12-D remains the formal benchmark. E4 is the robustness-qualified challenger. No historical parameter is allowed to change during forward accumulation.

Promotion requires newly accumulated observations. A reasonable first review point is after at least 60 new trading sessions; a stronger decision point is 120–252 sessions. Evaluation should compare return, MDD, Sharpe, volatility, turnover, realized cost drag, and signal stability without changing the frozen rules midstream.

## Initial run verification

- Historical build: PASS.
- Recent official TWSE supplement: PASS.
- Adjusted layer: PASS.
- Frozen D/E4 signal generation: PASS.
- Idempotent commit: PASS.
- Artifact upload: PASS.
- Full workflow conclusion: SUCCESS.

