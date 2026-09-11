# Sleeve-tilt dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen clips KEEP · live wire false  
Human: `OPEN Sleeve-tilt observe: SLEEVE_BELOW_MA60_a01`  
Default: **KEEP OBSERVE** · posture `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md`

Books: `LIVE_STACK` ∥ `SLEEVE_BELOW_MA60_a01`  
Execution: capital **500,000,000** · lot **1000**

Held-out vs `LIVE_STACK`:
- MDD↑pp: **0.0624505979783585**
- CAGR giveback pp: **-0.025375821461581793**
- Score: **0.049762687247567605**

Sealed vs `LIVE_STACK` (report-only):
- MDD↑pp: **-0.15437237900278733**
- CAGR giveback pp: **-0.07667458727487197**
- Score: **-0.19270967264022332**

## Reproduce

```bash
python3 scripts/e16_sleeve_tilt_dual_paper_ledgers.py
python3 scripts/e16_sleeve_tilt_month_end_monitor.py
```

Repro: `repro/sleeve-tilt-dual-paper-observe/`
