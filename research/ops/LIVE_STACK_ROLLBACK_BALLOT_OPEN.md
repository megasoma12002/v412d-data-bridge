# Live Stack Rollback — Ballot OPEN

Date: 2026-09-09  
Status: **OPEN** — live still **FINBAND [0.60, 0.90] + KD_OPT + `BLEND_E45_A05`** until ACCEPT  
Evidence: `LIVE_STACK_RERUN.md` · `repro/live-stack-rerun-20260909/`  
Authority: `HUMAN_DECISION_REGISTER.md` · prior ACCEPT notes `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md` · `E45_STITCH_ACCEPTED_BLEND_A05.md`

## Why this ballot

Post-cutover full paper re-run shows **NEW_LIVE worse than pre-big-win Soft-Frozen+KD**:

| book | held-out score vs OLD | tip (YTD/1y) |
|---|---:|---|
| `FINBAND_KD` (band only) | **+0.023** | PASS |
| `OLD_SF_KD_A05` (A05 only) | **−0.760** | ALERT |
| `NEW_LIVE` (FINBAND+KD+A05) | **−0.679** | ALERT |

Drag is **E45 A05 stitch**, not FINBAND. Absolute NEW_LIVE ~ CAGR **13.56%** / MDD **−22.05%** vs OLD ~ **13.94%** / **−21.77%**.

## Current live (until ACCEPT)

1. Soft-Frozen Financial **[0.60, 0.90]** (`FINBAND_F0.60-0.90`)  
2. FIN within-sleeve **`KD_OPT` KEEP**  
3. E45 **`BLEND_E45_A05` LIVE** (α=0.05)  
4. Capital **500M** · lot **1000** · DEFAULT **`E22_v2s_tw` KEEP**

## Reply with exactly one of

### A — ACCEPT rollback A05 only (**recommended**)

```
ACCEPT live-stack rollback: DROP_E45_A05
```

Effect: dedicated forward-only PR removes E45 stitch from `e21_forward_pipeline.py`.  
Soft-Frozen stays **[0.60, 0.90]** · KD_OPT KEEP. Paper target ≈ `FINBAND_KD` (near OLD).

### B — ACCEPT full restore to pre-big-win Soft-Frozen+KD

```
ACCEPT live-stack rollback: FULL_RESTORE_OLD_SF_KD
```

Effect: dedicated forward-only PR that (1) drops E45 A05 stitch **and** (2) reverts Soft-Frozen Financial clip to **[0.50, 0.95]**.  
KD_OPT KEEP · capital/lot/DEFAULT unchanged. Paper target ≈ `OLD_SF_KD`.

### C — ACCEPT revert FINBAND only (keep A05) — **not recommended**

```
ACCEPT live-stack rollback: REVERT_FINBAND_KEEP_A05
```

Effect: Soft-Frozen back to **[0.50, 0.95]**; A05 stays live. Paper ≈ `OLD_SF_KD_A05` (still tip ALERT / held-out −0.76).

### D — DEFER

```
DEFER live-stack rollback
```

### E — REJECT / keep current live

```
REJECT live-stack rollback
```

or

```
KEEP live-stack NEW_LIVE
```

## Recommendation

**`ACCEPT live-stack rollback: DROP_E45_A05`** — removes the measured drag; FINBAND edge is tiny (+0.02) and tip-clean, so full restore is optional.

## What ACCEPT does **not** include

- FIN within-sleeve change (KD_OPT stays)  
- Capital / board-lot / DEFAULT books change  
- History rewrite of `forward/e21`  
- Re-opening autumn / FIN micro-tune  
- New E45 stitch ACCEPT (would need a later dedicated ballot)

## Label

`LIVE_STACK_ROLLBACK_BALLOT_OPEN_2026-09-09__POST_RERUN__A05_DRAG`
