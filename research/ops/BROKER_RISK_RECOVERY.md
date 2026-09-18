# Broker risk / recovery / rate-limit — gap close vs public SPARK servers

Status: **OPS** — offline gates aligned with community practice  
Code: `scripts/broker_risk.py` · `scripts/broker_safety.py` · wired from `BrokerPreflightFillPort`  
Related: public ref [stock-broker-tw-server](https://github.com/Ye-Yu-Mo/stock-broker-tw-server)

## What landed

| Gap | Implementation |
|---|---|
| Order state machine | `OrderState` + `transition_order` → `broker_order_states.jsonl` |
| Startup reconcile | `run_startup_reconcile` → `broker_unresolved.json` (+ `stale` past trade date) |
| Manual resolve | `resolve_unresolved_order` (terminal FILLED/CANCELLED/REJECTED only) |
| Pre-submit risk | panic file · blacklist · qty / notional / price-deviation caps |
| Rate limit | rolling 60s write budget (`broker_rate_limit.jsonl`) |
| Circuit R/W split | open → writes blocked, reads ok |
| Half-open cooldown | `allow_circuit_write` / `record_circuit_success` (30s default) |
| Alerts | local `broker_alert_log.jsonl` + optional `E21_BROKER_ALERT_WEBHOOK` |

Unresolved orders **block** further live writes via `pre_submit_full_gate` until human resolve.

## Config

Optional `broker_preflight/broker_risk.json`:

```json
{
  "panic": false,
  "blacklist": [],
  "max_qty_shares": 50000,
  "max_notional": 5000000,
  "max_price_deviation": 0.15,
  "max_writes_per_minute": 30
}
```

Panic shortcut: `broker_panic.json` `{"panic": true}` or `set_panic(state_dir, True)`.

Circuit file `broker_circuit.json` modes: `closed` → `open` → `half_open` (after `cooldown_seconds`) → `closed` on success.

## Non-goals

- No SPARK DLL / network
- No Soft-Frozen ACCEPT flip
- No auto-cancel of stale orders without broker query (tagged `stale` only)
- Webhook delivery is best-effort fail-open

Label: `BROKER_RISK_RECOVERY__GAP_CLOSE`
