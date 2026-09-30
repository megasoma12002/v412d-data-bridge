# CUTOVER_CHECKLIST_TIPSOFT_IP3_LIVE_OVERRIDE

Date: 2026-09-30
Status: **AWAITING ACCEPT** (ballot OPEN · live flag still OFF)

## Why not wired yet

- Observe OPEN alone does not authorize cutover
- Human confirmed path: catch up live via ACCEPT Exact T+1 LIVE_OVERRIDE
- Need exact ACCEPT reply on `TIPSOFT_IP3_LIVE_OVERRIDE_ACCEPT_BALLOT_OPEN.md`

## Opened

- Observe: `OPEN paper observe: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 ...`
- ACCEPT ballot: `TIPSOFT_IP3_LIVE_OVERRIDE_ACCEPT_BALLOT_OPEN.md`

## Required before EXECUTED wire

1. [x] Dual-paper OPERATING (held +1.61 · tipY +6.04 · sealed −0.05)
2. [x] T+0 attribution `T0_NOT_DRIVER` (0kb5) — do not chase via T+0
3. [x] ACCEPT ballot OPEN with Path3 WITHIN coexistence explicit
4. [ ] Human exact ACCEPT reply
5. [ ] EXECUTED wire (`live_tipsoft_live_override=True`) + tests
6. Soft KEEP · Path4 OFF · broker false unless separate ACCEPT

Label: `CUTOVER_CHECKLIST_TIPSOFT_IP3_LIVE_OVERRIDE_2026-09-30__AWAITING_ACCEPT`
