# E45 Live Stitch — ROLLBACK ACCEPTED (DROP_E45_A05)

Date: 2026-09-09  
Human ballot: **`ACCEPT live-stack rollback: DROP_E45_A05`**  
Status: **ACCEPTED · LIVE UNWIRED (forward-only)**  
Prior ACCEPT: `E45_STITCH_ACCEPTED_BLEND_A05.md`  
Ballot: `LIVE_STACK_ROLLBACK_BALLOT_OPEN.md`  
Evidence: `LIVE_STACK_RERUN.md` (NEW_LIVE held-out −0.68 tip ALERT; A05 alone −0.76)

## What changed

| Field | Before | After |
|---|---|---|
| `LIVE_E45_STITCH` | `True` | **`False`** |
| Live book | `BLEND_E45_A05` | **none** |
| Soft-Frozen FIN | **[0.60, 0.90]** KEEP | KEEP |
| FIN within-sleeve | **KD_OPT** KEEP | KEEP |
| Capital / lot / DEFAULT | 500M / 1000 / `E22_v2s_tw` | KEEP |

Implementation: `scripts/e21_forward_pipeline.py` — no E45 exposure scale on Soft-Frozen sleeve targets.

## Why

Paper attribution after big-win cutover: A05 stitch was the measured drag; FINBAND alone was tip-clean ~+0.02 held-out vs pre-flip Soft-Frozen+KD.

## Forward-only

No `forward/e21` history wipe. Existing positions rebalance toward unscaled Soft-Frozen+KD_OPT targets as gaps appear.

## Non-actions

- No Soft-Frozen clip revert (that would need `FULL_RESTORE_OLD_SF_KD`)  
- No FIN within-sleeve change  
- No DEFAULT / capital change  
- No new E45 stitch without a later dedicated ACCEPT  

## Label

`E45_STITCH_ROLLBACK_ACCEPTED_2026-09-09__DROP_E45_A05__FORWARD_ONLY`
