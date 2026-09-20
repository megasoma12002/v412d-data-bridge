# Monday tip catch-up checklist (concrete ops + cashflow asserts)

Status: **OPS** — Soft-Frozen KEEP · no history rewrite  
When: first **weekday** after tip-align ACCEPT (tip still may show `E22_v2s_tw_effex`)  
Goal: confirm tip → `E22_v3_recv_pay_effdelay` (= realism **Phase 2**) so **View C** (cash + receivable) is live; then print three cashflow views.

Companion SSOT: `CASHFLOW_THREE_VIEWS.md`

## Do nothing this weekend

Do **not** invent a forward session or rewrite `forward/e21` history.

## Monday (after `v412f-forward-paper` green)

1. Open Actions → `V4.12-F E21 Daily Forward Paper` → latest run **success** (not `session_skip` only, unless typhoon/holiday).
2. Check tip books on Stage-E:
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
3. Cashflow three views (A / B / C″):
   ```bash
   python3 scripts/cashflow_three_views_report.py --write --fail-on-r4-identity
   # Expect: tip_lag false; View B identity_ok; View C may show receivables in ex→pay window
   ```
4. Confirm verify pack (auto-written by Phase 1; cashflow attached):
   ```bash
   python3 - <<'PY'
   import json
   from pathlib import Path
   v = json.loads(Path("research/ops/POST_FORWARD_E22_VERIFY.json").read_text())
   print("ok", v["ok"], "tip_lag", v["tip_lag"], "failures", v["failures"])
   assert v["ok"] is True
   assert v["tip_lag"] is False
   cf = v.get("cashflow_three_views") or {}
   print("cashflow attached", bool(cf), "warnings", (cf.get("warnings") or [])[:2])
   PY
   ```
5. Confirm alert scan no longer needs TIP_LAG as debt:
   ```bash
   python3 scripts/ops_alert_scan.py --report-only
   # TIP_LAG_BOOKS should be absent once tip == DEFAULT
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

`TIP_CATCHUP_MONDAY_CHECKLIST`
