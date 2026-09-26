# Backtest fill extreme + mechanism audit — Decision Pack

Date: 2026-09-26 · Generated `2026-09-26T15:06:25Z`
Status: **FILL_EXTREME_BACKTEST_DONE** · Soft-Frozen **KEEP** · live wire **false** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

Paper twin fills **6299** · ±5d mean distance to extreme **2.44%** · T+1 drag mean **0.789%** · COOL defend day-frac **16.02%**.

Primary structural driver remains **Exact T+1**. COOL on-book defense days are now visible across full history (unlike the short tip window which had full exposure).

## Binding

1. Soft-Frozen live KEEP — audit does not authorize clip flip
2. Exact T+1 KEEP — drag is by design
3. No tip history rewrite
4. No live wire from this backtest audit

Next: If human wants action: open a dedicated Stage A on ONE mechanism (e.g. soft-sell densify or KD season) — do not batch-retune from this audit

Label: `LIVE_FILL_EXTREME_BACKTEST_DECISION_PACK_2026-09-26__FILL_EXTREME_BACKTEST_DONE`

