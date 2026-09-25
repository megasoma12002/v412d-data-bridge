# ACCEPT — Deferred ops harden (review leftovers)

Status: **ACCEPTED** (human 2026-09-25: 「Accept刻意未动的部分」)  
Date: 2026-09-25  
Soft-Frozen: **KEEP** (clip / FUSE·DH / E45 stitch unchanged)

## Ballot

> `ACCEPT deferred ops harden from whole-repo review: (1) day-commit atomicity EXECUTE; (2) forward tip-write blast-radius harden EXECUTE; (3) broker live-write PREP charter only — flags stay False until UAT Login green + separate EXECUTE; (4) Stage-E full-history resim RESEARCH sandbox only — no forward/e21 history rewrite.`

## Scope matrix

| # | Item | This ACCEPT | Soft-Frozen tip |
|---|---|---|---|
| 1 | Partial-day ledger commit | **EXECUTE** — defer orders/signals/nav into `commit_day_books` (state last) | KEEP — fewer crash orphans |
| 2 | Daily forward `contents: write` push | **EXECUTE harden** — fail-closed if post-forward `ok!=true` before push; document blast radius | KEEP — tip still GHA-authored |
| 3 | Broker `API_WIRED` / live-write | **PREP only** — charter + ballot template; `broker_live_write_accepted=False`, `API_WIRED=False`, no `E21_BROKER_WRITE_LIVE` | KEEP |
| 4 | Historical method backtest | **RESEARCH sandbox** — Stage-E resim may write under `repro/` only | **No** `forward/e21` rewrite |

## Still forbidden without a new EXECUTE ballot

- Flip Soft-Frozen clip / KD_OPT / TEL_EQUAL / FUSE / DH
- `API_WIRED=True` or Yuanta `SendStockOrder` / SendAlgo
- `broker_live_write_accepted=True` + env live without UAT MsgCode evidence
- Merge R4 `settled_cash` → `portfolio_state.cash`
- Rewrite historical `forward/e21/nav.csv` (or invent tip)

## References

- Review debt: agent summary after #279
- Prior: `ACCEPT_OPS_RESIDUAL_FULL_FIX.md` · `ACCEPT_TIP_BOOKS_ALIGN_V3.md`
- Broker gates: `scripts/broker_safety.py` · `YUANTA_SPARK_*` howtos
- FinMind: `FINMIND_API_QUOTA_AND_RETRY.md`

Label: `ACCEPT_2026-09-25_DEFERRED_OPS_HARDEN`
