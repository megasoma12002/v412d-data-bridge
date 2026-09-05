# Odd-Lot Default Promote — Decision Pack

Date: 2026-09-05  
Status: **DRAFTED — AWAITING HUMAN ACCEPTANCE**  
Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Live default books today: **`E22_v2s`** (unchanged by this pack)

Authority: `HUMAN_DECISION_REGISTER.md` #6 · `ODD_LOT_PROMOTE_CHECKLIST.md` · `STRATEGY_UPDATE_STANDARD_PROCESS.md`  
Research closeout: `research/e22/GAP65_ODD_LOT_CLOSEOUT.md` · `research/e22/TW_ODD_LOT_APPLY.md`

## Purpose

Give humans a single accept/reject package to promote Taiwan odd-lot practice books  
**`E22_v2s_tw`** as the live **default**, without rewriting history or flipping Soft-Frozen.

This pack **does not** change `DEFAULT_BOOKS_VERSION`. Acceptance + dedicated promote PR required.

## What would change after accept + promote PR

| Item | Before | After |
|---|---|---|
| `DEFAULT_BOOKS_VERSION` | `E22_v2s` | `E22_v2s_tw` |
| Stock ex | Keep fractional float | `floor(shares_gross)` |
| Fractional remainder | Dust in shares | CIL cash `floor(frac × NT$10)` (yuan truncate) |
| Soft-Frozen clip | [0.50, 0.95] | **unchanged** |
| Exact T+1 | On | **unchanged** |
| `forward/e21` history | As committed | **no rewrite** — forward-only |

## Evidence already on main

| Gate | Status | Pointer |
|---|---|---|
| Named TW books implemented | DONE | `scripts/e22_dividend_accounting.py` (`E22_v2s_tw`) |
| Side-by-side vs v2s | DONE | ≈ **−0.0005 pp CAGR**; CIL cash ~153; end dust 0 |
| Research closeout | CLOSED | `GAP65_ODD_LOT_CLOSEOUT.md` |
| Promote checklist | DRAFTED | `ODD_LOT_PROMOTE_CHECKLIST.md` |
| Selectable on forward CLI | DONE | `e21_forward_pipeline.py --e22-version E22_v2s_tw` |
| Soft-Frozen KEEP asserted | YES | This pack + register #1 |

## Human decision ballot

Vote **one**:

| Ballot | Meaning | Next action |
|---|---|---|
| **ACCEPT promote** | Authorize changing live default to `E22_v2s_tw` | Open dedicated PR: set `DEFAULT_BOOKS_VERSION`; checklist all YES; forward-only |
| **ACCEPT research-only** | Keep named books; default stays `E22_v2s` | Close promote agenda; register #6 odd-lot stays DEFER |
| **REJECT** | Do not use TW CIL books | Keep v2s; document reason in register amendment |

Until ballot lands, treat odd-lot as **DEFER** (no silent default edit).

## Promote PR shape (only after ACCEPT promote)

1. Title: `Promote: DEFAULT_BOOKS_VERSION E22_v2s → E22_v2s_tw (odd-lot TW practice)`  
2. Body quotes this pack **ACCEPT** + `ODD_LOT_PROMOTE_CHECKLIST` all YES  
3. Single-purpose diff: default constant + ops one-liners  
4. Forbidden bundle: Soft-Frozen flip, L4/FIN50/BLEND cutover, tax/receivable books, E45 stitch, history rewrite  

## Explicit non-goals

- Board-lot 1000 as formal books  
- Market-mark CIL (`E22_v2s_cil`) as default  
- Backfill past NAV for CIL cash  
- Treating Gap 6.5 research closeout alone as live license  

## Label

`ODD_LOT_PROMOTE_DECISION_PACK_2026-09-05__AWAITING_HUMAN`
