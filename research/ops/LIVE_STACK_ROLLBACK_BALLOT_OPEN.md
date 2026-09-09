# Live Stack Rollback — Ballot EXECUTED (DROP_E45_A05)

Date: 2026-09-09  
Status: **EXECUTED** — live **FINBAND [0.60, 0.90] + KD_OPT · E45 stitch OFF**  
Human: **`ACCEPT live-stack rollback: DROP_E45_A05`**  
Cutover note: `E45_STITCH_ROLLBACK_ACCEPTED_DROP_A05.md`  
Evidence: `LIVE_STACK_RERUN.md` · `repro/live-stack-rerun-20260909/`

## Why

Post-cutover paper re-run: NEW_LIVE held-out **−0.68** tip ALERT vs OLD Soft-Frozen+KD; drag = **A05** (FINBAND alone ~+0.02 tip PASS).

## Chosen option

```
ACCEPT live-stack rollback: DROP_E45_A05
```

- Soft-Frozen **[0.60, 0.90] KEEP**  
- KD_OPT KEEP · capital 500M · lot 1000 · DEFAULT `E22_v2s_tw` KEEP  
- E45 **`BLEND_E45_A05` unwired** from `e21_forward_pipeline.py` (forward-only)

## Not chosen

- `FULL_RESTORE_OLD_SF_KD` (would also revert Soft-Frozen to [0.50, 0.95])  
- `REVERT_FINBAND_KEEP_A05`  
- DEFER / REJECT / KEEP NEW_LIVE  

## Label

`LIVE_STACK_ROLLBACK_BALLOT_EXECUTED_2026-09-09__DROP_E45_A05`
