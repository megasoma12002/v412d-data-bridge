# Telecom Within-Sleeve Optimize — Stage C (Research)

Date: 2026-09-08  
Status: **STAGE C COMPLETE** — `IMPROVE_VS_EQUAL` @ **500M**; `NO_IMPROVE` @ **3M**  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen: **KEEP**  
Live wire: **false** (does **not** auto-edit #126 `TEL_MIN_LOT_PACK`)

## Question

電信 within-sleeve 還能怎麼優化？各項數據有沒有比 `TEL_EQUAL` / 現行 `TEL_MIN_LOT_PACK` **變好**？

## Answer (short)

| Scale | vs `TEL_EQUAL` | vs live-intent `TEL_MIN_LOT_PACK` |
|---|---|---|
| **500M** | **有變好**：`TEL_DIVERSIFY_PACK` best (held-out score **+0.331**) | **有變好**：DIVERSIFY / SCORE 都贏 MIN_LOT |
| **3M** | **沒有**：全部 ≤0（與 Stage B STOP 一致） | EQUAL 仍較優 |

Top @ 500M: **`TEL_DIVERSIFY_PACK`** → then `TEL_SCORE_LOT_PACK` → then `TEL_MIN_LOT_PACK`.

## Policies tested

| id | Idea |
|---|---|
| `TEL_EQUAL` | BASE |
| `TEL_MIN_LOT_PACK` | Live-intent cheapest pack |
| `TEL_SCORE_LOT_PACK` | Score-first pack |
| `TEL_DIVERSIFY_PACK` | Cover names then equal remainder |
| `TEL_TOP2_EQUAL` / `TEL_TOP1` | Concentration |

## Next ballot (optional)

| Ballot | Effect |
|---|---|
| `KEEP live TEL_MIN_LOT_PACK` | No change to #126 |
| `ACCEPT live TEL_DIVERSIFY_PACK cutover` | Switch live within-Telecom policy |

Passing Stage C ≠ Soft-Frozen flip.

## Artifacts

- `TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C.md` / `.json`
- `repro/telecom-sleeve-optimize-20260908/`
- `scripts/e16_telecom_sleeve_optimize_stage_c.py`
