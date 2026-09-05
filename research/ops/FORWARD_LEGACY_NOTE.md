# Forward legacy config note

`forward/config.json` is a **legacy V4.12-F / E6-era shadow config**.

## Live authority (do not confuse)

| Role | Path |
|---|---|
| **Live stack** | `forward/e21/` via `scripts/e21_forward_pipeline.py` |
| Soft-Frozen clip | `scripts/e16_soft_frozen_base.py` → Financial **[0.50, 0.95]** |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

## Shadow sleeves (not live)

`forward/e6`, `forward/e9`, `forward/e10`, `forward/e10s2` and models listed in `forward/config.json` are **SHADOW / research**. They must not be read as the Soft-Frozen live book.

## Policy

- Do not edit `forward/config.json` to “point at” Soft-Frozen cutovers.
- Do not rewrite `forward/e21` history from legacy D/E4 signals.
- Month-end / cutover authority remains `research/STRATEGY_DEBT_BOARD.md`.
