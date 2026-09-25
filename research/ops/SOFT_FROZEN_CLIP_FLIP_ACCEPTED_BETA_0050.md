# Soft-Frozen Clip Flip — ACCEPTED (β densify / near-flat)

Date: 2026-09-25  
Human ballot (exact):

```
ACCEPT Soft-Frozen clip flip: F0.60-0.80_T0.03-0.35_E0.00-0.50
```

Status: **ACCEPTED · LIVE WIRED (forward-only)**  
Evidence: Stage A `BETA_0050_HIT` · human **接受近持平** paper observe · Class D ACCEPT this ballot  
SSOT: `scripts/e16_soft_frozen_base.py`

## Clip change

| Field | Before | After |
|---|---|---|
| FIN lo/hi | **[0.60, 0.90]** | **[0.60, 0.80]** |
| TEL | [0.03, 0.35] | unchanged |
| 0050 | [0.00, 0.35] | **[0.00, 0.50]** |
| START_WEIGHTS | `[0.90, 0.10, 0.00]` | `[0.80, 0.10, 0.10]` (in-envelope) |

## Paper evidence (pre-flip observe)

| Window | CAGR lift | MDD↑ |
|---|---:|---:|
| Held 2019+ | **+0.57pp** | −0.06pp (near-flat ACCEPT) |
| Sealed 2023+ | **+1.65pp** | **+0.50pp** |
| Tip YTD/1y MDD↑ | — | **+0.19pp** |

## Live stack after flip

Soft-Frozen clips (new) + **KD_OPT** + **TEL_EQUAL** + **FUSE_ADDITIVE** + **COOL_c8_f50_d21** · capital 500M · path `forward/e21/`  
β densify dual-paper observe → challenger **is** live Soft-Frozen (twin / superseded for promote).

## Non-actions

- No `forward/e21` tip history wipe/rewrite (forward-only)  
- Tip QC grandfather: dates `< 2026-09-25` may use prior FIN hi **0.90**; on/after ASOF enforce live **0.80** (`SOFT_FROZEN_PRIOR_FIN_HI` / `SOFT_FROZEN_CLIP_FLIP_ASOF`)  
- No DEFAULT books flip · no broker live-write from this ballot  
- No Soft/Sleeve/FUSE/COOL retune  
- No 公+民 universe expand  

## Artifacts

- Cutover: `CUTOVER_CHECKLIST_BETA_0050_DENSIFY.md` (**AUTHORIZED · LIVE WIRED**)  
- Prior observe: `BETA_0050_DENSIFY_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
- Posture: `BETA_0050_DENSIFY_OBSERVE_POSTURE.md`  

## Label

`SOFT_FROZEN_CLIP_FLIP_ACCEPTED_2026-09-25__F0.60-0.80_E0.00-0.50__FORWARD_ONLY`
