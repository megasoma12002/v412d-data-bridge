# Odd-Lot Default Promote — Decision Pack

Date: 2026-09-05  
Status: **ACCEPT promote** (human ballot 2026-09-05) — dedicated DEFAULT flip PR  
Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Live default books: **`E22_v2s_tw`** after promote PR merge (forward-only)

Authority: `HUMAN_DECISION_REGISTER.md` #6 · `ODD_LOT_PROMOTE_CHECKLIST.md` · `STRATEGY_UPDATE_STANDARD_PROCESS.md`  
Research closeout: `research/e22/GAP65_ODD_LOT_CLOSEOUT.md` · `research/e22/TW_ODD_LOT_APPLY.md`

## Purpose

Give humans a single accept/reject package to promote Taiwan odd-lot practice books  
**`E22_v2s_tw`** as the live **default**, without rewriting history or flipping Soft-Frozen.

Ballot **ACCEPT promote** cast 2026-09-05. This dedicated promote PR sets `DEFAULT_BOOKS_VERSION = E22_v2s_tw`.

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
| Promote checklist | **ALL YES** | `ODD_LOT_PROMOTE_CHECKLIST.md` |
| Selectable on forward CLI | DONE | `e21_forward_pipeline.py --e22-version E22_v2s_tw` |
| Soft-Frozen KEEP asserted | YES | This pack + register #1 |
| Par inventory (FIN+telecom) | **PASS** | TWSE `t187ap03_L` → all **VERIFIED NT$10** as-of 2026-09-04 (`PAR_VALUE_INVENTORY.md`) |
| 0050 ETF par | N/A | `ETF_RULES_LOOKUP_NEEDED` — not a Soft-Frozen equity CIL path |

## Human decision ballot — RESULT

| Ballot cast | Meaning | Next action |
|---|---|---|
| **ACCEPT promote** ✓ | Authorize live default → `E22_v2s_tw` | Dedicated promote PR (this change): `DEFAULT_BOOKS_VERSION`; checklist all YES; forward-only |

Park Item 1. Item 2 (tax/receivable) may open after this PR — not in this diff.

## Promote blocker — par value is data, not a constant

`E22_v2s_tw` must use per-code verified par (not a blind constant).

| Gate | Required before DEFAULT flip |
|---|---|
| Par inventory | Soft-Frozen FIN + telecom codes `VERIFIED` in `data/corporate_actions/par_value_by_code.csv` |
| Charter | `PAR_VALUE_LOOKUP_CHARTER.md` |
| Explicit risk waiver | Only if human ACCEPT with provisional-par risk — otherwise need VERIFIED rows |

**Today: `coverage_pass_for_promote = true`** (7/7 promote-gate equities VERIFIED @ NT$10 via TWSE).  
0050 ETF excluded from equity coverage. See `research/ops/PAR_VALUE_INVENTORY.md`.

**Future codes:** extend via `par_value_watchlist.csv` or  
`python3 scripts/e22_par_value_inventory.py --add-codes <codes> --fetch-twse`  
(`role=expand` — does not reopen promote gate / does not flip DEFAULT).

## Promote PR shape (only after ACCEPT promote + par gate)

1. Title: `Promote: DEFAULT_BOOKS_VERSION E22_v2s → E22_v2s_tw (odd-lot TW practice)`  
2. Body quotes this pack **ACCEPT** + `ODD_LOT_PROMOTE_CHECKLIST` all YES  
3. Single-purpose diff: default constant + ops one-liners  
4. Forbidden bundle: Soft-Frozen flip, L4/FIN50/BLEND cutover, tax/receivable books, E45 stitch, history rewrite  

## Taiwan practice note (2026-09-05 intake)

Source synthesis (Company Act / issuer notices / market commentary — research label only):

| Fact | Formal-books implication |
|---|---|
| 股票股利或現金增資產生 **<1 股** 畸零股 | Trigger for `E22_v2s_tw` floor + CIL |
| 法定／慣例：未滿 1 股按**面額**（原則 NT$10；少數彈性面額）折現現金；**算至元、元以下捨去** | Matches `floor(frac × par)` with default `par=10` |
| 高價股按面額折現 vs 市值落差大 → 小股東爭議常見 | **Do not** use market CIL as formal default; keep `E22_v2s_cil` research-only |
| 停止過戶前後常有**拼湊整股**期限（例：5 日內洽股代） | Ops/custody process — **not** portfolio alpha; optional future `E22_v3` window model only |
| 逾期未拼湊 → 強制面額現金；手續費／無實體劃撥可能實領近 0 | Optional haircut sensitivity — **not** default formal books |

Formal candidate stays **par CIL**. Modeling 拼湊 window or fee netting needs a **separate** charter — out of this promote.

## Explicit non-goals

- Board-lot 1000 as formal books  
- Market-mark CIL (`E22_v2s_cil`) as default (would “fix” high-price controversy in the wrong direction for legal books)  
- Simulating 拼湊整股 as strategy edge  
- Backfill past NAV for CIL cash  
- Treating Gap 6.5 research closeout alone as live license  

## Label

`ODD_LOT_PROMOTE_DECISION_PACK_2026-09-05__AWAITING_HUMAN`
