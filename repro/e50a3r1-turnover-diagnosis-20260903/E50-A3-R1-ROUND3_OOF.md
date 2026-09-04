# E50-A3-R1 Round-3 OOF Challenger Screen

## Hypothesis

Prefer higher OOF bootstrap margin among dual-gate passers (book-size neighborhood), keeping turnover ≤ 2.5% with headroom. Round-2 used turnover-first and left this region unused for held-out.

## Decision

**`OOF_NEW_DUAL_GATE_WINNER`** → lock **C3**

```
top_k=25
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
```

| | C1 | C2 | C3 |
|---|---:|---:|---:|
| OOF turnover | 2.20% | 2.01% | 2.11% |
| OOF bootstrap | 0.767 | 0.755 | **0.808** |

Held-out: see `E50-A3-R1-C3_HELDOUT.md` → **`MIXED_HELDOUT`** (validation bootstrap still fails; worse than C2).
