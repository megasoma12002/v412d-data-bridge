# Yuanta SPARK adapter skeleton (offline)

Status: **OPS / RESEARCH** — mapping only; **no DLL / no network**  
Code: `scripts/yuanta_spark_adapter.py` · tests: `tests/test_yuanta_spark_adapter.py`  
UAT jump VM: `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`  
Gates: `scripts/broker_safety.py` · Soft-Frozen KEEP until ACCEPT  
Live seam: `BrokerPreflightFillPort._write_spark_offline_intents` in `live_fill_broker.py`

## Module boundary

| Module | Responsibility | Must not |
|---|---|---|
| `yuanta_spark_adapter` | shares↔張 · B/S · BasketNo · StockOrder intent shape · OnResponse→ack map | import pythonnet / YuantaSparkAPI · flip live write |
| `live_fill_broker` | session gate · fixture acks · Soft-Frozen write gates · call offline intent writer | own SPARK field math |
| `broker_safety` / `broker_risk` | confirm+reserve · circuit · dedupe · ballot | know SPARK DLL types |

`send_stock_order_live()` always raises `SparkNotWiredError` while `API_WIRED=False`.

## What this is

Offline field mapper between Soft-Frozen pending orders and 元大 SPARK `StockOrder` / `SendStockOrder` OnResponse shapes:

| Soft-Frozen / safety | SPARK |
|---|---|
| shares (`quantity`) | `OrderQty` = 張 (`shares // 1000`) |
| `BUY` / `SELL` | `B` / `S` |
| `client_order_id` | `BasketNo` ≤ 32 alnum (hash if needed) |
| `order_id` | ack `order_id` + map via basket log |
| — | `APCode=0` 一般整股 · `OrderType="0"` 現貨 |

Artifacts under `broker_preflight/`:

- `spark_intents_{asof}.json` — INTENT_ONLY payloads (`api_wired: false`)
- `spark_basket_map.jsonl` — BasketNo ↔ client_order_id

`BrokerPreflightFillPort` already emits these next to generic `submit_intents_*.json`.

## Hard non-goals (this PR)

- Does **not** `pip install pythonnet` or load `YuantaSparkAPI.dll`
- Does **not** call `Open` / `Login` / `SendStockOrder`
- Does **not** flip `LIVE.broker_live_write_accepted`
- Does **not** write Soft-Frozen `fills.csv` by itself

## Next ACCEPT steps (human)

1. UAT fixed IP + Login/query on jump VM  
2. Wire pythonnet client behind `confirm_and_reserve_broker_submit`  
3. Map OnResponse → `broker_acks` → existing fill port  
4. Separate ACCEPT for Soft-Frozen live write  

Label: `YUANTA_SPARK_ADAPTER__OFFLINE_SKELETON`
