# Sleeve-tilt dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen clips KEEP · live wire false  
Human: `OPEN Sleeve-tilt observe: SLEEVE_RSI14_LT30_a0225`  
Default: **KEEP OBSERVE** · posture `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md`

Books: `LIVE_STACK` ∥ `SLEEVE_RSI14_LT30_a0225`  
Execution: capital **500,000,000** · lot **1000**

Held-out vs `LIVE_STACK`:
- MDD↑pp: **0.10431108645896359**
- CAGR giveback pp: **0.011170605362398334**
- Score: **0.09872578377776442**

Sealed vs `LIVE_STACK` (report-only):
- MDD↑pp: **0.03523233762379174**
- CAGR giveback pp: **0.005434792058167659**
- Score: **0.03251494159470791**

## Reproduce

```bash
python3 scripts/e16_sleeve_tilt_dual_paper_ledgers.py
python3 scripts/e16_sleeve_tilt_month_end_monitor.py
```

Repro: `repro/sleeve-tilt-dual-paper-observe/`
