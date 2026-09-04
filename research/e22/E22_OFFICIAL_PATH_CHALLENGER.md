# E22 Official-Path Challenger

**Recommendation:** `RECOMMEND_WIRE_E22_DIVIDENDS_INTO_OFFICIAL_EXEC_PATH_VIA_NEW_VERSION`

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| E16_E18 | 7.22% | -22.77% | -0.0417 |
| E16_E18_E22 | 11.19% | -22.11% | 0.0013 |

- CAGR lift: **3.97 pp**
- MDD change: 0.66 pp

## How to merge (no in-place rewrite)

1. Challenger forward package with dividend credits on `cash_ex_date`
2. Paper parallel vs live E21
3. Explicit approval → new SOFT_FROZEN E22 version

Does **not** edit `scripts/e21_forward_pipeline.py` or append rewritten history to `forward/e21/`.

## Paper package (executed 2026-09-04)

- Script: `scripts/e22_challenger_forward_pipeline.py`
- Ledgers: `forward/e22_challenger/` (QC **PASS**)
- Extended bootstrap **2026-07-01 → 2026-09-03** (46 sessions): **~84k** dividend cash credited on 5 ex-dates
- Promotion package: `research/e22/E22_PROMOTION_PACKAGE.md` → **`AWAITING_EXPLICIT_HUMAN_APPROVAL`** for `E22_v2_CASH_EX_OFFICIAL_PATH`
- Next: human signs approval phrase; do not cut over or rewrite `forward/e21/` until then
