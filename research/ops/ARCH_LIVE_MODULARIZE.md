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
| `pyproject.toml` + `setup.py` | Installable `e21-ops` (flat `scripts/*.py` as top-level modules) |
| `Dockerfile` | Ops image (`pip install -e .`; no broker secrets) |

## Install (no `sys.path` hacks)

```bash
pip install -e .
python3 -c "import live_config; print(live_config.LIVE.capital)"
python3 scripts/e21_qc.py --state-dir forward/e21
```

CI uses `pip install -e .` instead of `PYTHONPATH=scripts`. Hygiene bans new `sys.path.insert/append` under `scripts/` and `tests/`.

## Explicit non-goals (modularize + pyproject)

- Soft-Frozen clip / LIVE_FUSE / LIVE_DH values
- Broker API credentials / live order routing
- Merging paper `simulate_core` with live session
- Migrating every month-end monitor (COMPARE-family first; four wrappers on `DualPaperMonitorSpec`)

## Next (optional)

1. Migrate remaining direct-pair monitors onto `DualPaperMonitorSpec`
2. Shared dual-paper ledger driver on `simulate_core`
3. Cloud long-run deploy of the Docker ops image (GCP asia-east1 candidate)
4. Broker port behind `live_execution` fill schema (dry-run first; 元大 SPARK ≠ repo 元大股息抓取)

Label: `ARCH_LIVE_MODULARIZE_2026-09-14__CONFIG_STRATEGY_EXEC_LEDGER__MONITOR_RUNNER__PYPROJECT`
