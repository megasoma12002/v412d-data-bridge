# R4 / R5 week-1 observe checklist

Status: **OPS** — after merge of gap-close S3/R4/R5/P4 (#240)  
Soft-Frozen / Exact T+1 / `E22_v2s_tw_effex` **KEEP** — no books flip this week.

## Goal

Run **one trading week** of observe-only T+2 estimate (R4). Run R5 only when a custody / broker statement fixture is available. Then decide **one** follow-up ACCEPT ballot: receivable formal books **or** broker live write — not both.

## Daily (after `v412f-forward-paper`)

**Phase 3 continuous observe (LANDED):** `ops_alert_scan.py` emits `R4_ESTIMATE_PRESENT` / `R4_ESTIMATE_MISSING` / `TIP_LAG_BOOKS` — `settled_cash_estimate` is **liquidity view NOT NAV**.


1. Confirm job green (or `session_skip` on closed board — OK).
2. Artifact present: `forward/e21/settlement_cash_estimate.csv` + `.json`.
3. Spot-check summary fields (liquidity view, **not** NAV):
   - `settling_today_net`
   - `unsettled_net`
   - `paper_cash` vs `settled_cash_estimate`
4. Do **not** treat `settled_cash_estimate` as portfolio cash or cutover signal.

## When to run R5

Only if you have a same-day (or settle-date) custody export / fixture:

```bash
PYTHONPATH=scripts python3 scripts/twse_t2_broker_reconcile.py \
  --estimate forward/e21/settlement_cash_estimate.csv \
  --custody path/to/custody.csv \
  --asof YYYY-MM-DD \
  --out-dir forward/e21/broker_reconcile
```

Expect `all_ok: true` within `tol` (default NT$1). Mismatches → investigate fee/min-commission / slip vs exchange print — still observe-only.

## Optional overlays (same week, still observe)

| Trigger | Command / file |
|---|---|
| Typhoon / board postpone | `twse_same_day_ex_list.py` → `data/dividend_events/ex_date_amendments.csv` |
| Payment 重大訊息 | `e22_mops_payment_amendments.py` → `mops_payment_amendments.csv` |

Do not rewrite Soft-Frozen dividend ledgers without a separate ACCEPT (these CLIs have no ``--write-ledger`` flag).

## End-of-week decision gate

Pick **at most one** ballot (or **neither** / KEEP observe):

| Ballot | Open if… | Still forbidden without extra ACCEPT |
|---|---|---|
| **Receivable formal** (`E22_v3_*` promote path) | Ops needs spendable-cash / pay-date identity; dual-paper ready | Silent flip of Soft-Frozen DEFAULT |
| **Broker live** (`fill_port=broker` + ACCEPT + `E21_BROKER_WRITE_LIVE`) | Stable ack path + preflight OPEN + `broker_safety` (lock / dedupe / confirm) green | Inventing fills; env-only live write; orphan acks; concurrent live write without lock; Soft-Frozen cutover without ACCEPT |

Defer if R4 noise is high, R5 never ran, or no ops owner for the ballot.

## Pointers

- Estimate: `scripts/twse_t2_settlement_estimate.py`
- Reconcile: `scripts/twse_t2_broker_reconcile.py`
- Charters: `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md` · `TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md`
- Live fill default stays `paper` (`live_config.LIVE.fill_port`)
