# E50-A3-R1 Round-2 OOF Challenger Screen

## Hypothesis

Around locked C1 (`exit_multiple=2.0`), widen exit buffer / add mild stabilizers on **2011–2018 OOF only** to create turnover headroom while keeping bootstrap ≥ 0.70.

## Decision

**`OOF_NEW_DUAL_GATE_WINNER`** → lock **C2**

```
top_k=20
rebalance_every=42
exit_multiple=2.5
neutralization=NONE
industry_cap=5
min_hold_cycles=0
replace_rank_gap=0
```

| | C1 (reference) | C2 (new) |
|---|---:|---:|
| OOF turnover | 2.20% | **2.01%** |
| OOF bootstrap | 0.767 | 0.755 |
| OOF CAGR | 10.04% | 9.91% |
| OOF MDD | -30.07% | -31.09% |

18 new dual-gate passers (excluding C1). Selection: lowest OOF turnover among new dual-gate passers.

Held-out for C2: see `E50-A3-R1-C2_HELDOUT.md` → **`MIXED_HELDOUT`**.
