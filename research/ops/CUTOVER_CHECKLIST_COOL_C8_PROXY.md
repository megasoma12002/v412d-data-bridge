# Cutover Checklist — COOL_c8_f50_d21

Status: **AUTHORIZED · LIVE WIRED (2026-09-25)**  
Soft-Frozen **KEEP** · forward-only

## Required before any live ACCEPT — DONE

- [x] Paper dual-observe OPEN/OPERATING (`COOL_C8_PROXY_*`)
- [x] Stack vs replace trial: **不疊** preferred (`COOL_C8_DH_FUSE_STACK_TRIAL`)
- [x] Human dedicated ballot: `ACCEPT Live cutover: COOL_c8_f50_d21（ replace DH、keep FUSE）。`
- [x] Stacking policy locked: **REPLACE DH · KEEP FUSE** (DH+COOL both True refused)

## Live flags

- `LIVE_FUSE_ADDITIVE=True`
- `LIVE_DH_EXPOSURE=False` (replaced)
- `LIVE_COOL_EXPOSURE=True` · id `COOL_c8_f50_d21`
- Ballot: `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`

## Non-actions

- No Soft-Frozen tip rewrite  
- No broker live-write until separate ACCEPT  
- No re-enable DH without dedicated ACCEPT  

## Label

`CUTOVER_CHECKLIST_COOL_C8_PROXY_2026-09-25__AUTHORIZED_LIVE_REPLACE_DH_KEEP_FUSE`
