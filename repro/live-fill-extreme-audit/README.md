# Live fill extreme + mechanism audit repro

Charter: `research/ops/LIVE_FILL_EXTREME_AUDIT_CHARTER.md`

## Tip path
Screen: `reports/LIVE_FILL_EXTREME_AUDIT_SCREEN.md`  
Decision: `reports/LIVE_FILL_EXTREME_AUDIT_DECISION_PACK.md`

```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py
```

Verdict: **`FILL_EXTREME_AUDIT_DONE`** · Soft-Frozen KEEP · no live wire.

## Backtest path (FUSE+COOL live twin)
Screen: `reports/LIVE_FILL_EXTREME_BACKTEST_SCREEN.md`  
Decision: `reports/LIVE_FILL_EXTREME_BACKTEST_DECISION_PACK.md`

```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py
```

Verdict: **`FILL_EXTREME_BACKTEST_DONE`** · Soft-Frozen KEEP · no live wire.

## Deep dive A–D (T+1 / KD / CLIP / COOL)
Screen: `reports/LIVE_FILL_MECH_DEEPDIVE_SCREEN.md`  
Decision: `reports/LIVE_FILL_MECH_DEEPDIVE_DECISION_PACK.md`

```bash
PYTHONPATH=scripts python3 scripts/live_fill_mech_deepdive.py
```

Verdict: **`FILL_MECH_DEEPDIVE_DONE`** · Soft-Frozen KEEP · no live wire.
