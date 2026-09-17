# Broker risk / recovery / rate-limit — gap close vs public SPARK servers

Status: **OPS** — offline gates aligned with community practice  
Code: `scripts/broker_risk.py` · wired from `BrokerPreflightFillPort`  
Related: `broker_safety.py` · public ref [stock-broker-tw-server](https://github.com/Ye-Yu-Mo/stock-broker-tw-server)

## What landed

| Gap | Implementation |
|---|---|
| Order state machine | `OrderState` + `transition_order` → `broker_order_states.jsonl` |
| Startup reconcile | `run_startup_reconcile` → `broker_unresolved.json` |
| Manual resolve | `resolve_unresolved_order` (terminal FILLED/CANCELLED/REJECTED only) |
| Pre-submit risk | panic file · blacklist · qty / notional / price-deviation caps |
| Rate limit | rolling 60s write budget (`broker_rate_limit.jsonl`) |
| Circuit R/W split | `circuit_access`: open circuit → **writes blocked, reads ok** |
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

## Non-goals

- No SPARK DLL / network
- No Soft-Frozen ACCEPT flip
- Webhook delivery is best-effort fail-open

Label: `BROKER_RISK_RECOVERY__GAP_CLOSE`
