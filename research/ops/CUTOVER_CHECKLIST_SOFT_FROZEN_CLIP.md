# Soft-Frozen Clip Flip — Cutover Checklist (Class D)

Date: 2026-09-09  
Status: **DRAFTED — NOT AUTHORIZED**  
Human ballot: `SOFT_FROZEN_CLIP_FLIP_BALLOT_DRAFT.md`  
Soft-Frozen live: **KEEP** until ACCEPT PR  

## Gates

| # | Gate | Current | Pass? |
|---|---|---|---|
| 1 | Clip-search charter ACCEPT + Stage B candidates locked | YES | **YES** |
| 2 | 500M rescreen vs live Soft-Frozen+KD_OPT exists | `SOFT_FROZEN_CLIP_500M_RESCREEN.md` | **YES** |
| 3 | Chosen id held-out score > 0 @ 500M | FINBAND_F0.60-0.90 ≈ **+0.023**; Stage B TEL floors **≤0** | **WEAK / YES only for FINBAND** |
| 4 | Tip YTD+1y PASS vs BASE @ 500M | FINBAND tip PASS; Stage B #1 tip ALERT | **YES for FINBAND** |
| 5 | Stage E observe OPEN (recommended) | ballot OPEN; observe not yet wired | **NO** |
| 6 | ≥1 clean month-end on observe id | not yet | **NO** |
| 7 | Soft-Frozen SSOT path identified (`e16_soft_frozen_base.py`) | YES | **YES** |
| 8 | FIN band change only if ACCEPT names FINBAND_* | Policy | Policy |
| 9 | No bundle with E45 stitch / FIN50 / L4 / books | Policy | Policy |
| 10 | Dedicated Class D ACCEPT string cast | Not cast | **NO** |

## Recommended id (if any)

`FINBAND_F0.60-0.90` — **tiny** edge only; **not** 「大勝」.  
Stage B TEL/ETF top-K: **do not flip** on 500M+KD_OPT evidence.

## Non-actions until ACCEPT

- Do **not** edit Soft-Frozen constants  
- Do **not** stitch E45  
- Do **not** rewrite `forward/e21` history  

## Label

`CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP_2026-09-09__DRAFTED_NOT_AUTHORIZED`
