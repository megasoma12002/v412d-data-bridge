# Soft-assist dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen KEEP · live wire false  
Human: `OPEN Soft-assist observe: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05`  
Prior challenger (superseded): `SOFT_CHAMP_PLUS_K9_LT30_a10`  
Default: **KEEP OBSERVE** · posture `SOFT_ASSIST_OBSERVE_POSTURE.md`

Books: `LIVE_KD_OPT` ∥ `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05`  
Buy soft: `BELOW_MA120@1+K9_LT30@1` · sell soft: `RSI6_GT80@0.5`  
Execution: capital **500,000,000** · lot **1000**

Held-out vs `LIVE_KD_OPT`:
- MDD↑pp: **0.10121715777380302**
- CAGR giveback pp: **0.00045014447767055543**
- Score: **0.10099208553496775**

Sealed vs `LIVE_KD_OPT` (report-only):
- MDD↑pp: **0.33846485153506967**
- CAGR giveback pp: **0.04656330651648943**
- Score: **0.31518319827682495**

## Reproduce

```bash
python3 scripts/e16_soft_assist_dual_paper_ledgers.py
python3 scripts/e16_soft_assist_month_end_monitor.py
```

Repro: `repro/soft-assist-dual-paper-observe/`
