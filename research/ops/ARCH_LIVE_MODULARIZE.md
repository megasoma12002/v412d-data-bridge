# Live architecture modularization (2026-09-14)

Status: **OPS / ENGINEERING** — Soft-Frozen **KEEP** · live flags unchanged  
PR scope: extract seams for Docker / future broker adapter — **no strategy cutover**

## Modules

| Module | Role |
|---|---|
| `scripts/live_config.py` | `LiveConfig` / `LIVE_*` / `KD_OPT` / books / capital SSOT |
| `scripts/live_strategy_targets.py` | Soft-Frozen features + FUSE/DH/E45 overlays |
| `scripts/live_execution.py` | Pending fills at open (Exact T+1) |
| `scripts/live_ledger.py` | Immutable CSV append + holdings |
| `scripts/e21_forward_pipeline.py` | CLI + day orchestration (re-exports flags) |
| `scripts/ops_dual_paper_month_end.py` | Parameterized dual-paper month-end runner |
| `scripts/live_kd_guard.py` | Research ledger KD / E45-stitch fail-closed |

## Explicit non-goals (this change)

- Soft-Frozen clip / LIVE_FUSE / LIVE_DH values
- Broker API / Docker image
- Merging paper `simulate_core` with live session
- Migrating every month-end monitor (COMPARE-family first)

## Next (optional)

1. Migrate remaining direct-pair monitors onto `DualPaperMonitorSpec`
2. Shared dual-paper ledger driver on `simulate_core`
3. Installable package (`pyproject`) + Docker ops image
4. Broker port behind `live_execution` fill schema

Label: `ARCH_LIVE_MODULARIZE_2026-09-14__CONFIG_STRATEGY_EXEC_LEDGER__MONITOR_RUNNER`
