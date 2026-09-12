# Soft-Frozen Clip Flip — Cutover Checklist (Class D)

Date: 2026-09-09  
Status: **ACCEPTED · LIVE WIRED (forward-only)**  
Human ballot: **`ACCEPT Soft-Frozen clip flip: FINBAND_F0.60-0.90`**  
Acceptance note: `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md`  
Soft-Frozen live Financial clip: **[0.60, 0.90]** (SSOT `scripts/e16_soft_frozen_base.py`)

## Gates (at ACCEPT)

| # | Gate | Current | Pass? |
|---|---|---|---|
| 1 | Clip-search charter ACCEPT + Stage B candidates locked | YES | **YES** |
| 2 | 500M rescreen vs live Soft-Frozen+KD_OPT exists | `SOFT_FROZEN_CLIP_500M_RESCREEN.md` | **YES** |
| 3 | Chosen id held-out score > 0 @ 500M | FINBAND_F0.60-0.90 ≈ **+0.023**; Stage B TEL floors **≤0** | **YES for FINBAND** |
| 4 | Tip YTD+1y PASS vs BASE @ 500M | FINBAND tip PASS | **YES for FINBAND** |
| 5 | Stage E observe OPEN | OPEN then promoted to live wire | **YES** |
| 6 | Clean month-end / tip hygiene on FINBAND | tip PASS at ACCEPT | **YES** |
| 7 | Soft-Frozen SSOT path identified (`e16_soft_frozen_base.py`) | YES | **YES** |
| 8 | FIN band change only if ACCEPT names FINBAND_* | ACCEPT named FINBAND | **YES** |
| 9 | No bundle with FIN50 / L4 / books flip | books/DEFAULT KEEP | **YES** |
| 10 | Dedicated Class D ACCEPT string cast | Cast 2026-09-09 | **YES** |

## Live result

| Field | Before | After |
|---|---|---|
| FIN lo/hi | [0.50, 0.95] | **[0.60, 0.90]** |
| TEL / 0050 clips | unchanged | unchanged |
| DEFAULT books | `E22_v2s_tw` | KEEP |
| KD_OPT / TEL_EQUAL | KEEP | KEEP |

Stage B TEL/ETF top-K candidates: **not** flipped (held-out ≤0).

## Non-actions (still)

- Do **not** rewrite `forward/e21` history  
- Do **not** treat this page as license to flip FIN50 / L4 / BLEND_025 / Soft-assist / Sleeve-tilt  
- Do **not** re-open clip search without a new charter  

## Label

`CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP_2026-09-09__ACCEPTED_FINBAND_LIVE`
