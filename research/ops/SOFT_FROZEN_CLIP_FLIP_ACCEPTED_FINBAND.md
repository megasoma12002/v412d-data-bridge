# Soft-Frozen Clip Flip — ACCEPTED (FINBAND_F0.60-0.90)

Date: 2026-09-09  
Human ballot: **`ACCEPT Soft-Frozen clip flip: FINBAND_F0.60-0.90`** (via「請都做」)  
Also: **`OPEN Soft-Frozen clip observe: FINBAND_F0.60-0.90`**  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

## Clip change

| Field | Before | After |
|---|---|---|
| FIN lo/hi | **[0.50, 0.95]** | **[0.60, 0.90]** |
| TEL | [0.03, 0.35] | unchanged |
| 0050 | [0.00, 0.35] | unchanged |

SSOT: `scripts/e16_soft_frozen_base.py`

## Observe

Stage E observe id **`FINBAND_F0.60-0.90`** is now the **live Soft-Frozen FIN band**.  
Paper screen evidence: `SOFT_FROZEN_FIN_BAND_500M_SCREEN.md` (held-out ~+0.02 tip PASS — small edge).

## Co-bundled (same human「請都做」)

- Live FIN within-sleeve **KD_OPT KEEP**
- E45 stitch **`BLEND_E45_A05`** — see `E45_STITCH_ACCEPTED_BLEND_A05.md`

## Non-actions

- No `forward/e21` history wipe/rewrite  
- No DEFAULT books flip  
- No FIN within-sleeve retune beyond existing KD_OPT  

## Label

`SOFT_FROZEN_CLIP_FLIP_ACCEPTED_2026-09-09__FINBAND_F0.60-0.90__FORWARD_ONLY`
