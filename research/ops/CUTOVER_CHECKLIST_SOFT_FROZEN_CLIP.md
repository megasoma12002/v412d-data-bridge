# Soft-Frozen Clip Flip — Cutover Checklist (Class D)

Date: 2026-09-25  
Status: **ACCEPTED · LIVE WIRED (forward-only)** — latest flip  
Human ballot: **`ACCEPT Soft-Frozen clip flip: F0.60-0.80_T0.03-0.35_E0.00-0.50`**  
Acceptance note: `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_BETA_0050.md`  
Prior FINBAND ACCEPT (2026-09-09): `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md` (superseded for live bounds)

Soft-Frozen live clips: **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]**  
SSOT: `scripts/e16_soft_frozen_base.py`

## Live result (2026-09-25)

| Field | Before | After |
|---|---|---|
| FIN lo/hi | [0.60, 0.90] | **[0.60, 0.80]** |
| TEL | [0.03, 0.35] | unchanged |
| 0050 | [0.00, 0.35] | **[0.00, 0.50]** |
| START_WEIGHTS | [0.90, 0.10, 0.00] | **[0.80, 0.10, 0.10]** |
| Overlays | FUSE + COOL KEEP | KEEP |
| DEFAULT books | tip E22_v3 KEEP | KEEP |

## Non-actions

- No tip history rewrite · no broker live-write · no Soft/Sleeve/COOL retune

## Label

`CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP_2026-09-25__BETA_0050_LIVE_WIRED`
