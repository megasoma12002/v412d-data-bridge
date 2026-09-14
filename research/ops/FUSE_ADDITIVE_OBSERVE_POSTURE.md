# FUSE_ADDITIVE Posture — LIVE WIRED + paper shadow

Date: 2026-09-13 (updated after live cutover)  
Status: **LIVE WIRED** (2026-09-13 ACCEPT) · paper dual-ledger **may continue as shadow**  
Soft-Frozen **clips KEEP [0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **DH_dd06** co-wired  
Challenger ID: **`FUSE_ADDITIVE`**  
Ballot: `LIVE_DH_FUSE_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`  
Human ACCEPT: **`ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE`**

## Binding

1. Live path `forward/e21` uses Soft observe softs + Sleeve RSI tilt via `LIVE_FUSE_ADDITIVE=True`.  
2. Paper dual-ledger `LIVE_STACK` ∥ `FUSE_ADDITIVE` may continue as **shadow** (not a second live book).  
3. Soft-assist and Sleeve-tilt **independent** observes remain paper KEEP — **do not** ops-auto-fuse them outside the FUSE recipe.  
4. Soft-Frozen clip / KD / TEL unchanged by this posture alone.

## Operating paths

| Role | Path |
|---|---|
| Live wire | `scripts/e21_forward_pipeline.py` · `scripts/live_dh_fuse_cutover.py` |
| Paper ledgers | `scripts/e16_fuse_additive_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_fuse_additive_month_end_monitor.py` |
| Pack | `scripts/ops_month_end_paper_pack.py` |

## Hard non-actions

- No Soft-Frozen clip flip from this page  
- No silent Soft∥Sleeve merge of **independent** observe IDs (FUSE is the dedicated joint recipe)  
- No KD / TEL change from this page alone  

## Rollback

```python
LIVE_FUSE_ADDITIVE = False
# typically with LIVE_DH_EXPOSURE = False for full MENU3 rollback
```

## Label

`FUSE_ADDITIVE_POSTURE_2026-09-13__LIVE_WIRED__PAPER_SHADOW_OK`
