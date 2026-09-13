# Live cutover ballot — EXECUTED ACCEPT (DH_dd06 + FUSE_ADDITIVE)

Date: 2026-09-13  
Human ballot (exact intent): **`ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE`**  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Satisfies (combined) the blocked cutover checklists:

- `CUTOVER_CHECKLIST_FUSE_ADDITIVE.md` → AUTHORIZED  
- `CUTOVER_CHECKLIST_E45_DEFEND_HANDOFF.md` → AUTHORIZED for **DH_dd06 exposure**

## Live recipe (MENU3 paper twin)

| Layer | Value |
|---|---|
| Soft-Frozen FIN clip | **[0.60, 0.90] KEEP** |
| FIN within-sleeve | **`KD_OPT` KEEP** |
| TEL within-sleeve | **`TEL_EQUAL` KEEP** |
| Sleeve targets | **`FUSE_ADDITIVE`** = Soft softs + Sleeve RSI14 α=0.225 |
| Risk overlay | **`DH_dd06_vz1p0`** (dd=6%, vz=1.0, shrink=0.50) |
| Soft∥Sleeve ops auto-fuse | **N/A** — this is dedicated FUSE ACCEPT, not silent merge of independent observes |

## Implementation

- `scripts/e21_forward_pipeline.py` — `LIVE_FUSE_ADDITIVE=True`, `LIVE_DH_EXPOSURE=True`
- `scripts/live_dh_fuse_cutover.py` — paper-faithful FUSE offense NAV → DH exposure
- `scripts/fuse_additive_helpers.py` / `e45_defend_handoff_helpers.py` — `LIVE_WIRE=True`
- `scripts/e21_qc.py` — DH-aware weight / Soft-Frozen clip checks
- Forward-only — no `forward/e21` history wipe/replay

## Rollback

Set in `e21_forward_pipeline.py`:

```python
LIVE_FUSE_ADDITIVE = False
LIVE_DH_EXPOSURE = False
```

Restores Soft-Frozen + KD_OPT + TEL_EQUAL live stack (pre-FUSE/DH).

## Non-actions

- Soft-Frozen clip flip  
- Soft∥Sleeve independent-observe auto-merge without FUSE recipe  
- Capital / board-lot / E22 books change  

## Label

`LIVE_DH_FUSE_CUTOVER_ACCEPTED_2026-09-13__DH_dd06_FUSE_ADDITIVE__FORWARD_ONLY`
