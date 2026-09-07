# Soft-Frozen TEL + 0050 floors → 10% — 2026-09-07

Human ballot: **「ACCEPT 電信 0050下限 10%」**  
Financial clip **[0.50, 0.95] unchanged**. E45 stitch **FORBIDDEN**.

## Clip change (single source `scripts/e16_soft_frozen_base.py`)

| Sleeve | Before | **After (ACCEPT)** |
|---|---|---|
| Financial | [0.50, 0.95] | **[0.50, 0.95]** KEEP |
| Telecom | [0.03, 0.35] | **[0.10, 0.35]** |
| 0050 | [0.00, 0.35] | **[0.10, 0.35]** |

Also updated in-envelope `START_WEIGHTS` / regime priors (Bull/Sideways start at 80/10/10).

## Follow-through

- Live wipe+replay `forward/e21` @ 15M + board-lot 1000 with new targets
- Active dual-paper observe `--refresh-ledgers`
- QC: `soft_frozen_tel_clip` / `soft_frozen_etf_clip` fail-closed

## Paper sensitivity (pre-cutover, BASE @ 15M board-lot)

TEL-only floor 10% (ETF still 0) already improved full MDD ≈1.8pp vs 3% TEL floor.  
This ACCEPT also floors **0050 at 10%** — live/paper numbers from the post-ACCEPT replay are authoritative.
