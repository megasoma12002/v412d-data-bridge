# Fill mechanism deep dive A–D (paper / observe)

Date: 2026-09-26  
Status: **Stage A observe `FILL_MECH_DEEPDIVE_DONE`** · Soft-Frozen live **KEEP** · no live wire  
Human: 全面分析後再討論後續（T+1／KD／CLIP／COOL）

Prerequisite audits:
- Tip: `LIVE_FILL_EXTREME_AUDIT_*`
- Backtest twin: `LIVE_FILL_EXTREME_BACKTEST_*`

Scope: re-slice existing tip + FUSE+COOL backtest fill detail into four blocks; add offense vs COOL NAV windows for D.

| Block | Question |
|---|---|
| A T+1 | sleeve×side, windows, drag buckets, corr(T+1, ±5d) |
| B KD | FIN in-season (Apr15–May15) vs off; windows; BUY/SELL |
| C CLIP | FIN `CLIP_FIN_HI` vs not; cross with KD |
| D COOL | defend vs off fills; sleeve; NAV giveback vs MDD improve |

**Deep dive ≠ live change · ≠ Soft-Frozen flip · ≠ tip rewrite.**

```bash
PYTHONPATH=scripts python3 scripts/live_fill_mech_deepdive.py
```

Artifacts: `research/ops/LIVE_FILL_MECH_DEEPDIVE_*` · `repro/live-fill-extreme-audit/reports/`
