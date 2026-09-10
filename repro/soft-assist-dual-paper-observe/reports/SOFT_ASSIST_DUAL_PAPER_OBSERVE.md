# Soft-assist dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen KEEP · live wire false  
Human: `OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80`  
Default: **KEEP OBSERVE** · posture `SOFT_ASSIST_OBSERVE_POSTURE.md`

Books: `LIVE_KD_OPT` ∥ `SOFT_BOTH__BELOW_MA120__RSI6_GT80`  
Execution: capital **500,000,000** · lot **1000**

Held-out vs `LIVE_KD_OPT`:
- MDD↑pp: **0.0787053514347269**
- CAGR giveback pp: **-0.019362856897719993**
- Score: **0.0690239229858669**

Sealed vs `LIVE_KD_OPT` (report-only):
- MDD↑pp: **0.3314240000340307**
- CAGR giveback pp: **0.0947677493835064**
- Score: **0.2840401253422775**

## Reproduce

```bash
python3 scripts/e16_soft_assist_dual_paper_ledgers.py
python3 scripts/e16_soft_assist_month_end_monitor.py
```

Repro: `repro/soft-assist-dual-paper-observe/`
