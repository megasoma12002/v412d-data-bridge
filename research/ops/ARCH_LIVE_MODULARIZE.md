# Live architecture modularization (2026-09-14)

Status: **OPS / ENGINEERING** — Soft-Frozen **KEEP** · live flags unchanged  
PR scope: extract seams for Docker / future broker adapter — **no strategy cutover**

## Modules

| Module | Role |
|---|---|
| `scripts/live_config.py` | `LiveConfig` / `LIVE_*` / `KD_OPT` / books / capital SSOT |
| `scripts/live_strategy_targets.py` | Soft-Frozen features + FUSE/DH/E45 overlays |
| `scripts/live_execution.py` | Pending fills at open (Exact T+1) — `FillPort` / paper / dry_run |
| `scripts/live_ledger.py` | Immutable CSV append + holdings |
| `scripts/e21_forward_pipeline.py` | CLI + day orchestration (re-exports flags; `--fill-port`) |
| `scripts/ops_dual_paper_month_end.py` | Parameterized dual/multi-paper month-end runner |
| `scripts/ops_dual_paper_ledgers.py` | Shared dual/multi-paper ledger driver on `simulate_core` (`chal_market` / `post_base` / `sim_context`) |
| `scripts/live_kd_guard.py` | Research ledger KD / E45-stitch fail-closed |
| `pyproject.toml` + `setup.py` | Installable `e21-ops` (flat `scripts/*.py` as top-level modules) |
| `Dockerfile` + `docker-compose.yml` | Ops image (`pip install .`; no broker secrets) |
| `scripts/ops_docker_qc_smoke.sh` | Build image + `e21_qc` bind-mount smoke |

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

- Soft-Frozen clip / LIVE_FUSE / LIVE_DH values
- Broker API credentials / live order routing
- Merging paper `simulate_core` with live session
- Silent unify of `E22_V2S` vs `E22_v2s_tw`

## Docker ops QC (B1)

Image packages tooling only (no broker secrets). `forward/` + `data/` stay on the host via bind mount (see `.dockerignore`).

```bash
bash scripts/ops_docker_qc_smoke.sh
# or: docker compose build && docker compose run --rm qc
```

CI: `.github/workflows/docker-ops-qc-smoke.yml`. **Who writes `forward/e21`:** still GHA `v412f-forward-paper` (not the container) until an explicit deploy cutover.

## Fill ports (C1/C2)

`scripts/live_execution.py`: `FillPort` protocol · `PaperOpenFillPort` (default) · `DryRunFillPort` (shadow under `broker_dryrun/`, no live `fills.csv`).

```bash
# default / live canonical path — paper only
python3 scripts/e21_forward_pipeline.py
# research dry-run (non-canonical state copy)
E21_FILL_PORT=dry_run python3 scripts/e21_forward_pipeline.py \
  --allow-noncanonical-paths --state-dir /tmp/e21-dry --market ...
```

True broker adapter (Shioaji / SPARK / …) maps exchange acks → same fill row schema; credentials never in image/git.

## Next (optional)

1. Cloud long-run deploy of the Docker ops image (GCP asia-east1 candidate; pick single writer for `forward/e21`)
2. One broker skeleton behind `FillPort` (dry-run map first; 元大 SPARK ≠ repo 元大股息抓取)
3. TWSE session calendar (holidays / typhoon) — charter `TWSE_SESSION_CALENDAR_CHARTER.md`; **required before broker live submit**

Label: `ARCH_LIVE_MODULARIZE__DOCKER_QC__FILL_PORT`
