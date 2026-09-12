# Soft-Assist Observe Posture — LOCKED (KEEP OBSERVE)

Date: 2026-09-11  
Status: **LOCKED** · **OPERATING OBSERVE** · default **KEEP OBSERVE**  
Soft-Frozen **KEEP** · live **`KD_OPT` HOLD** (no Soft-assist wire) · E45 **OFF**  
Challenger: **`SOFT_CHAMP_PLUS_K9_LT30_a10`** (supersedes `SOFT_BOTH__BELOW_MA120__RSI6_GT80`)

## Binding

1. Maintain dual-paper `LIVE_KD_OPT` ∥ `SOFT_CHAMP_PLUS_K9_LT30_a10`.  
2. Month-end monitor via pack (`soft_assist_month_end`).  
3. **No live Soft-assist** without dedicated cutover ACCEPT for **this** challenger ID.  
4. Soft-Frozen / TEL / KD season-K params unchanged from this posture.  
5. Sleeve-tilt observe stays independent (no auto Soft-assist×sleeve combo).

## Operating paths

| Role | Path |
|---|---|
| Ledgers | `scripts/e16_soft_assist_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_soft_assist_month_end_monitor.py` |
| Pack | `scripts/ops_month_end_paper_pack.py` |

## Hard non-actions

- No Soft-Frozen flip  
- No silent live Soft-assist wire  
- No KD micro-tune from this observe  
- No E45 stitch  
- No hard AND reopen  

## Promote gate

Month-end paper gates: `MONTH_END_PROMOTE_GATE_CHECKLIST.md` (Soft-assist column).  
Tip stays clean + held-out lift holds → at most `READY_FOR_DEDICATED_ACCEPT_BALLOT` → then dedicated cutover ACCEPT (`CUTOVER_CHECKLIST_SOFT_ASSIST.md`, currently **BLOCKED**). **No live wire from the month-end page.**

## Label

`SOFT_ASSIST_OBSERVE_POSTURE_2026-09-11__KEEP_OBSERVE__K9_PLUS__LIVE_KD_KEEP`
