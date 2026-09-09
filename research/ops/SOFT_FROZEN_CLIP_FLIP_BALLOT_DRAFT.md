# Soft-Frozen Clip Flip — Ballot Draft (Class D)

Date: 2026-09-09  
Status: **DRAFTED / NOT AUTHORIZED** — do **not** treat as ACCEPT  
Checklist: `CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP.md`  
Soft-Frozen live today: **KEEP [0.50, 0.95]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]**

## Purpose

Exact human reply strings for a **dedicated** Soft-Frozen clip flip PR.  
Stage B + 500M rescreen evidence is **necessary but not sufficient**.

## Pre-ballot (operator)

1. Prefer Stage E observe OPEN + ≥1 clean tip print on the chosen id.  
2. Confirm checklist gates reviewed.  
3. Confirm FIN band stays Soft-Frozen unless explicitly named in ACCEPT.  
4. Confirm no bundle with E45 stitch / FIN50 / L4 / books flip.

## Reply with exactly one of

### A — ACCEPT flip (pick one id)

```
ACCEPT Soft-Frozen clip flip: FINBAND_F0.60-0.90
```

```
ACCEPT Soft-Frozen clip flip: CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.05-0.35
```

```
ACCEPT Soft-Frozen clip flip: CLIP_SEARCH_F0.50-0.95_T0.10-0.35_E0.00-0.35
```

```
ACCEPT Soft-Frozen clip flip: CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.00-0.35
```

Effect: opens dedicated PR editing `scripts/e16_soft_frozen_base.py` to the named box.  
**Warning (2026-09-09):** @ 500M+KD_OPT, Stage B TEL/ETF ids have **held-out ≤ 0**; FIN-band best is only **~+0.02**. Class D is **not** a large-win lever on current evidence.

### B — DEFER

```
DEFER Soft-Frozen clip flip
```

### C — REJECT

```
REJECT Soft-Frozen clip flip
```

## What ACCEPT does **not** include

- E45 live stitch  
- FIN within-sleeve change (live KD_OPT KEEP)  
- DEFAULT books flip  
- Capital change  
- Bundling FIN50 / L4 / BLEND cutovers  

## Label

`SOFT_FROZEN_CLIP_FLIP_BALLOT_DRAFT_2026-09-09__NOT_AUTHORIZED__SOFT_FROZEN_KEEP`
