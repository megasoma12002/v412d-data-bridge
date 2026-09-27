# Broker / R5 / OCO — PREP not open

Date: 2026-09-27  
Status: **PREP_NOT_OPEN** · Soft-Frozen **KEEP** · Exact T+1 **KEEP**  
Ballot posture: build surfaces **without** EXECUTE / `API_WIRED` / Soft-Frozen `fill_port=broker`

## Human ask

> 真下單、T+2 對帳全自動化、條件單 — 能先做不開啟

**Yes.** This pack lands observe / INTENT_ONLY scaffolding only. No SendStockOrder, no SendAlgo, no live fill write.

## Three tracks

| Track | PREP surface | Still blocked |
|---|---|---|
| **真下單** | `yuanta_spark_adapter` StockOrder intents · `BrokerPreflightFillPort` offline intents · `ops_broker_r5_oco_prep_status.py` | `API_WIRED` · `broker_live_write_accepted` · `E21_BROKER_WRITE_LIVE` · ballot JSON · Soft-Frozen non-paper fill |
| **T+2 對帳自動化** | `ops_r5_observe_auto.py` · `fixtures/r5_custody_dropin.csv` (optional drop-in) · alert codes `R5_*` · existing `r5-broker-reconcile.yml` | Merging R5 into NAV · auto promote broker |
| **條件單 OCO** | `build_oco_strategy_intent` / `write_spark_oco_intents` / `send_algo_oco_live` → always `SparkNotWiredError` | Any `SendAlgoCOOdrStrategy` |

## Operator

```bash
pip install -e .
# Gate + OCO + optional R5 smoke (synthetic if no drop-in):
python3 scripts/ops_broker_r5_oco_prep_status.py --run-r5 --fail-if-gates-open
# When real custody arrives:
# cp /path/to/export.csv fixtures/r5_custody_dropin.csv
python3 scripts/ops_r5_observe_auto.py
python3 scripts/ops_alert_scan.py --report-only
```

## EXECUTE still requires (separate human ballot)

See `ACCEPT_PREP_BROKER_LIVE_WRITE_2026-09-25.md` + new `ACCEPT EXECUTE broker live-write …`.  
UAT Login MsgCode `0001`/`00001` first. OCO SendAlgo is a **further** ACCEPT after stock-order smoke.

## Explicit non-goals

- Flip Soft-Frozen tip to broker fills  
- Weekend invent tip / rewrite history  
- Auto tax DEFAULT / NHI live  
- Treat R5 green as strategy cutover  

## Refs

- `YUANTA_SPARK_ADAPTER_SKELETON.md` · `YUANTA_SPARK_CONDITIONAL_OCO_NOTES.md`  
- `PHASE_4_R5_SCAFFOLD_LANDED_2026-09-20.md` · `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md`  
- Status JSON: `BROKER_R5_OCO_PREP_STATUS.json` (generated)

Label: `BROKER_R5_OCO_PREP_NOT_OPEN_2026-09-27`
