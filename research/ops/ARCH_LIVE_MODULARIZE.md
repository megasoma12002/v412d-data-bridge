# Live architecture modularization (2026-09-19)

Status: **OPS / ENGINEERING** — Soft-Frozen **KEEP** · live flags unchanged  
PR scope: extract seams for Docker / future broker adapter — **no strategy cutover · no ACCEPT / API_WIRED**

## Modules

| Module | Role |
|---|---|
| `scripts/live_config.py` | `LiveConfig` / `LIVE_*` / `KD_OPT` / books / capital SSOT |
| `scripts/live_strategy_targets.py` | Soft-Frozen features + FUSE/DH/E45 overlays |
| `scripts/live_execution.py` | **Facade** — `resolve_fill_port` / `fill_pending_at_open` (stable imports) |
| `scripts/live_fill_core.py` | Paper / dry_run ports · `sort_*_sell_before_buy` · `afford < orig_q` skip |
| `scripts/live_fill_broker.py` | `BrokerPreflightFillPort` (offline acks + SPARK intent seam) |
| `scripts/live_session_io.py` | Canonical path gates · market/state load · asof rewind refuse |
| `scripts/live_e22_day.py` | One-day E22 books apply helper |
| `scripts/live_rebalance_orders.py` | Sleeve gap → Soft-Frozen order rows (SELL-before-BUY) |
| `scripts/live_day_commit.py` | Deferred fills/divs + atomic `portfolio_state` + Excel audit |
| `scripts/live_ledger.py` | Immutable CSV append + holdings + commission helpers |
| `scripts/e21_forward_pipeline.py` | CLI + day orchestration only (thin) |
| `scripts/e50_early_stack_combined_nav.py` | Research sim — shared `sort_rows_sell_before_buy` |
| `scripts/yuanta_spark_adapter.py` | Offline SPARK field map (`API_WIRED=False`) |
| `scripts/ops_observe_helpers.py` | Stage-E / R4 / receivable helpers shared by cashflow + alert scan |
| `scripts/ops_dual_paper_month_end.py` | Parameterized dual/multi-paper month-end runner |
| `scripts/ops_dual_paper_ledgers.py` | Shared dual/multi-paper ledger driver on `simulate_core` |
| `scripts/live_kd_guard.py` | Research ledger KD / E45-stitch fail-closed |
| `pyproject.toml` + `setup.py` | Installable `e21-ops` (flat `scripts/*.py` as top-level modules) |
| `Dockerfile` + `docker-compose.yml` | Ops image (`pip install .`; no broker secrets) |
| `scripts/ops_docker_qc_smoke.sh` | Build image + `e21_qc` bind-mount smoke |

## Day orchestration (call graph)

```
e21_forward_pipeline.main
  ├─ live_session_io          (paths / market / preflight)
  ├─ live_strategy_targets    (features / session targets)
  ├─ live_execution           → live_fill_core | live_fill_broker
  ├─ live_e22_day             (dividends / receivables)
  ├─ live_rebalance_orders    (orders.csv rows)
  └─ live_day_commit          (fills + state + audit Excel)
```

Stable call sites keep `from live_execution import …`. Soft-Frozen KEEP.

## Install (no `sys.path` hacks)

```bash
pip install -e .
python3 -c "import live_config; print(live_config.LIVE.capital)"
python3 scripts/e21_qc.py --state-dir forward/e21
```

CI uses `pip install -e .` instead of `PYTHONPATH=scripts`. Hygiene bans new `sys.path.insert/append` under `scripts/` and `tests/`.

## Month-end monitors → `DualPaperMonitorSpec`

All scheduled `*_month_end_monitor.py` scripts are thin wrappers (see prior section in git history / #233).

## Dual-paper ledgers → `DualPaperLedgerSpec`

Shared driver: `scripts/ops_dual_paper_ledgers.py` (`prepare` → `simulate_core` → CSV/compare → report).

| Family | Spec | Notes |
|---|---|---|
| E45 exposure (dual / A05 / A25 / sleeve-local) | `DualPaperLedgerSpec` + `prepare_e45_exposure_pair` | default E22 books |
| Soft-assist / Sleeve-tilt / FUSE_ADDITIVE | `DualPaperLedgerSpec` + `live_kd_sim_kwargs` | Soft-Frozen [0.60,0.90] assert · LIVE_KD guard |
| FINCAP50 / BLEND_025 / L4 | `DualPaperLedgerSpec` | **explicit `E22_V2S`** (do not silently unify to TW) |
| FIN within-sleeve (3 challengers) | `MultiPaperLedgerSpec` | EQUAL ∥ RS ∥ MIX_L75 ∥ KD_OPT |
| M2 BIL_FX | `DualPaperLedgerSpec` + `PreparedBooks.chal_market` | CHAL on BIL×USDTWD augmented panel |
| defend-handoff DH_dd06 | `DualPaperLedgerSpec` + `post_base` | two-pass: BASE NAV → exposure → CHAL |
| 民營 native | `DualPaperLedgerSpec` + `sim_context` | extended market + PRIV FIN/ALL patch |

Pack CLI paths unchanged (`ops_month_end_paper_pack.py --refresh-ledgers`).

## Explicit non-goals

- Soft-Frozen clip / LIVE_FUSE / LIVE_DH values (KEEP)
- Broker API credentials / live order routing / `API_WIRED=True`
- Re-enabling E45 A05 live stitch (DROPPED)
- Silent unify of research `E22_V2S` callers vs live DEFAULT

## Fill policy align (ACCEPT 2026-09-19)

Paper `simulate_core` and live `_paper_fill_rows` both **skip** underfunded BUY when `afford < orig_q` (paper requeues pending). Ballot: `ACCEPT_PAPER_LIVE_FILL_SKIP_ALIGN.md`.

## Docker ops QC (B1)

Image packages tooling only (no broker secrets). `forward/` + `data/` stay on the host via bind mount (see `.dockerignore`).

```bash
bash scripts/ops_docker_qc_smoke.sh
# or: docker compose build && docker compose run --rm qc
```

CI: `.github/workflows/docker-ops-qc-smoke.yml`. **Who writes `forward/e21`:** still GHA `v412f-forward-paper` (not the container) until an explicit deploy cutover.

## Fill ports

| Port | Module | Behavior |
|---|---|---|
| `paper` (default) | `live_fill_core.PaperOpenFillPort` | Exact T+1; deferred `fills.csv` until day-commit |
| `dry_run` | `live_fill_core.DryRunFillPort` | Shadow under `broker_dryrun/`; no live fills |
| `broker` | `live_fill_broker.BrokerPreflightFillPort` | Session gate + fixture acks; SPARK intents via adapter |

```bash
# default / live canonical path — paper only
python3 scripts/e21_forward_pipeline.py
# research dry-run (non-canonical state copy — Soft-Frozen forward/e21 refuses non-paper)
E21_FILL_PORT=dry_run python3 scripts/e21_forward_pipeline.py \
  --allow-noncanonical-paths --state-dir /tmp/e21-dry --market ...
```

True broker adapter (元大 SPARK) maps exchange acks → same fill row schema; credentials never in image/git. Soft-Frozen `forward/e21` always requires `paper` even with `--allow-noncanonical-paths`. See `YUANTA_SPARK_ADAPTER_SKELETON.md`.

## SPARK adapter boundary

| Layer | Owns |
|---|---|
| `yuanta_spark_adapter` | Field map · BasketNo · INTENT_ONLY artifacts · `assert_not_wired` |
| `live_fill_broker` | Session / ballot / circuit / ack→fill · calls adapter offline seam only |
| `broker_safety` / `broker_risk` | Submit reserve · dedupe · live write gates |

`API_WIRED` stays `False` until a separate ACCEPT.

## Next (optional)

1. Cloud long-run deploy of the Docker ops image (GCP asia-east1 candidate; pick single writer for `forward/e21`)
2. Wire pythonnet client behind `confirm_and_reserve_broker_submit` (UAT first) — see `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`
3. TWSE session calendar (holidays / typhoon) — `TWSE_SESSION_CALENDAR_CHARTER.md`; **required before broker live submit**
4. T+2 settlement cash **estimate** (observe-only) — `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md`

Label: `ARCH_LIVE_MODULARIZE__FILL_CORE__DAY_COMMIT`
