# Monday tip catch-up — cashflow number asserts

Status: **OPS** — Soft-Frozen KEEP · no history rewrite  
Goal: tip → `E22_v3_recv_pay_effdelay` so **View C** (cash + receivable) is live; then print three cashflow views.

Companion SSOT: `CASHFLOW_THREE_VIEWS.md`

## Do nothing this weekend

Do **not** invent a forward session or rewrite `forward/e21` history.

## Monday (after `v412f-forward-paper` green)

1. Tip books on Stage-E:
   ```bash
   python3 - <<'PY'
   import json
   from pathlib import Path
   ps = json.loads(Path("forward/e21/portfolio_state.json").read_text())
   print("last_date", ps.get("last_date"))
   print("e22_books_version", ps.get("e22_books_version"))
   assert ps.get("e22_books_version") == "E22_v3_recv_pay_effdelay"
   PY
   ```
2. Cashflow three views (A / B / C″):
   ```bash
   python3 scripts/cashflow_three_views_report.py --write --fail-on-r4-identity
   # Expect: tip_lag false; View B identity_ok; View C may show receivables in ex→pay window
   ```
3. Post-forward pack:
   ```bash
   python3 - <<'PY'
   import json
   from pathlib import Path
   v = json.loads(Path("research/ops/POST_FORWARD_E22_VERIFY.json").read_text())
   print("ok", v["ok"], "tip_lag", v["tip_lag"])
   assert v["ok"] is True
   assert v["tip_lag"] is False
   cf = v.get("cashflow_three_views") or {}
   print("cashflow attached", bool(cf), "warnings", (cf.get("warnings") or [])[:2])
   PY
   ```

## Read the numbers

| View | Field | Use |
|---|---|---|
| A | paper Exact T+1 `cash` | NAV cash leg |
| B | R4 `settled_cash_estimate` | Spendable liquidity ≠ NAV |
| C″ | `cash + e22_receivables` | Dividend timing under TAX0 |

## If tip still lags after a green open session

1. File ops note (pipeline not reading `LIVE.e22_books_version`) — **do not** backfill NAV.  
2. Soft-Frozen KEEP · keep running three-views report (warnings expected).

## Label

`TIP_CATCHUP_MONDAY_CASHFLOW_ASSERTS`
