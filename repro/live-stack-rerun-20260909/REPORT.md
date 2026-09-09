# Live stack paper re-run (post DROP_E45_A05)

Generated: `2026-09-09T12:52:23.827736+00:00`
Capital **500,000,000** · lot **1000** · KD_OPT · Soft-Frozen live **[0.6, 0.9]** · E45 stitch **OFF**
Improvement vs retired A05: **IMPROVED** (see `LIVE_STACK_IMPROVE_STATUS.md`)

## Absolute

| book | full CAGR | full MDD | heldout CAGR | heldout MDD | sealed CAGR | sealed MDD |
|---|---:|---:|---:|---:|---:|---:|
| `OLD_SF_KD` | 13.94% | -21.77% | 18.26% | -21.77% | 25.22% | -12.95% |
| `CURRENT_LIVE` | 13.92% | -21.72% | 18.20% | -21.72% | 25.17% | -12.81% |
| `OLD_SF_KD_A05` | 13.59% | -22.15% | 17.48% | -22.15% | 24.18% | -11.33% |
| `RETIRED_FINBAND_A05` | 13.56% | -22.05% | 17.46% | -22.05% | 24.12% | -11.28% |

## vs OLD_SF_KD (pre big-win)

| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |
|---|---:|---:|---:|---|---|---|
| `CURRENT_LIVE` | 0.023 | 0.050 | 0.055 | PASS | PASS | True |
| `OLD_SF_KD_A05` | -0.760 | -0.375 | 0.771 | ALERT | ALERT | False |
| `RETIRED_FINBAND_A05` | -0.679 | -0.279 | 0.800 | ALERT | ALERT | False |

## Improvement vs RETIRED_FINBAND_A05

| metric | value |
|---|---|
| held-out score lift | **+0.701** |
| tip restored (ALERT→PASS) | **True** |
| full CAGR Δ | +0.36 pp |
| full MDD improve | +0.329 pp |
| status | **IMPROVED** |

## Verdict

CURRENT_LIVE (FINBAND+KD, E45 OFF after DROP_E45_A05) vs OLD_SF_KD held-out score=+0.023 tip_clean=True YTD=PASS 1y=PASS. vs RETIRED_FINBAND_A05: held-out lift=+0.701 tip_restored=True status=IMPROVED. Live Soft-Frozen=[0.6, 0.9]; LIVE_E45_STITCH=False.

Repro: `repro/live-stack-rerun-20260909/`
