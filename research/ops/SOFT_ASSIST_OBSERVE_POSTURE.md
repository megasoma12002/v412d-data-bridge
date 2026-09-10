# Soft-Assist Observe Posture — LOCKED (KEEP OBSERVE)

Date: 2026-09-10  
Status: **LOCKED** · **OPERATING OBSERVE** · default **KEEP OBSERVE**  
Soft-Frozen **KEEP** · live **`KD_OPT` HOLD** (no Soft-assist wire) · E45 **OFF**

## Binding

1. Maintain dual-paper `LIVE_KD_OPT` ∥ `SOFT_BOTH__BELOW_MA120__RSI6_GT80`.  
2. Month-end monitor via pack (`soft_assist_month_end`).  
3. **No live Soft-assist** without dedicated cutover ACCEPT.  
4. Soft-Frozen / TEL / KD season-K params unchanged from this posture.

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

## Promote gate

Tip stays clean + held-out lift holds → dedicated cutover ACCEPT (checklist `CUTOVER_CHECKLIST_SOFT_ASSIST.md`, currently **BLOCKED**).

## Label

`SOFT_ASSIST_OBSERVE_POSTURE_2026-09-10__KEEP_OBSERVE__LIVE_KD_KEEP`
