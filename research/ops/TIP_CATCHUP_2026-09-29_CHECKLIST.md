# Tip catch-up checklist — next session **2026-09-29**

Status: **PENDING** — Soft-Frozen KEEP · no weekend invent · no history rewrite  
Why not Monday 9/28: TWSE **CLOSED_HOLIDAY**（孔子誕辰／教師節）· 9/25 中秋 · 9/26–27 週末  
Tip frozen at: **`2026-09-24`** until first green open session after holidays  
Goal: forward tip → stamp live cutovers that landed while board was closed

Companion: `TIP_CATCHUP_MONDAY_CHECKLIST.md` (Phase 2 books catch-up pattern) · calendar `data/calendars/twse_sessions_2026.csv`

## Do nothing until 2026-09-29 open

Do **not** invent a tip day for 9/25–28. Session gate must `session_skip`.

## After `v412f-forward-paper` green on **2026-09-29**

1. Confirm run is a real session (not skip-only):
   - Actions → E21 Daily Forward Paper → success with tip advance
2. Assert tip date + live stamps:
   ```bash
   python3 scripts/tip_catchup_assert_929.py
   # or:
   python3 - <<'PY'
   import json
   from pathlib import Path
   ps = json.loads(Path("forward/e21/portfolio_state.json").read_text())
   assert ps.get("last_date") == "2026-09-29", ps.get("last_date")
   assert ps.get("e22_books_version") == "E22_v3_recv_pay_effdelay"
   assert ps.get("cool_exposure_live") is True
   assert ps.get("dh_exposure_live") is False
   assert ps.get("conf_ret3_631l_live") is True
   assert ps.get("fin_priv_v7_f05_live") is True
   assert "BETA" in str(ps.get("soft_frozen_clip_flip") or "")
   print("tip stamps OK", ps.get("last_nav"))
   PY
   ```
3. Cashflow three views:
   ```bash
   python3 scripts/cashflow_three_views_report.py --write --fail-on-r4-identity
   ```
4. QC + post-forward verify + alerts:
   ```bash
   python3 scripts/e21_qc.py --state-dir forward/e21
   python3 scripts/ops_alert_scan.py --report-only
   ```
5. Holdings drift note (expect rebalance under `REBALANCE_L1_MIN=0.05`):
   - Pre-holiday tip FIN ~87% lot drift vs Soft-Frozen ~75% target — 9/29 may emit SELL/BUY rows
6. Optional R5 if custody drop-in ready:
   ```bash
   python3 scripts/ops_r5_observe_auto.py --asof 2026-09-29
   ```

## Pass criteria

| Check | Expect |
|---|---|
| `last_date` | `2026-09-29` |
| books | `E22_v3_recv_pay_effdelay` |
| COOL live / DH live | True / False |
| CONF_RET3 / FinPriv / TEL_T3 stamps | present True |
| clip stamp | β densify (not FINBAND-only) |
| Exact T+1 QC | PASS |
| tip invent 9/25–28 | **none** |

## Evidence file (after pass)

Write `research/ops/TIP_CATCHUP_2026-09-29.md` with run id + assert output (ops owner).

Label: `TIP_CATCHUP_2026-09-29_CHECKLIST__PENDING_NEXT_SESSION`
