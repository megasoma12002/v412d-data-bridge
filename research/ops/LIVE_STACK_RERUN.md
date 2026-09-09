# Live stack paper re-run (post FINBAND + E45 A05)

Generated: `2026-09-09T12:06:32.092527+00:00`
Capital **500,000,000** · lot **1000** · KD_OPT · Soft-Frozen live **[0.6, 0.9]**

## Absolute

| book | full CAGR | full MDD | heldout CAGR | heldout MDD | sealed CAGR | sealed MDD |
|---|---:|---:|---:|---:|---:|---:|
| `OLD_SF_KD` | 13.94% | -21.77% | 18.26% | -21.77% | 25.22% | -12.95% |
| `FINBAND_KD` | 13.92% | -21.72% | 18.20% | -21.72% | 25.17% | -12.81% |
| `OLD_SF_KD_A05` | 13.59% | -22.15% | 17.48% | -22.15% | 24.18% | -11.33% |
| `NEW_LIVE` | 13.56% | -22.05% | 17.46% | -22.05% | 24.12% | -11.28% |

## vs OLD_SF_KD (pre big-win)

| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |
|---|---:|---:|---:|---|---|---|
| `FINBAND_KD` | 0.023 | 0.050 | 0.055 | PASS | PASS | True |
| `OLD_SF_KD_A05` | -0.760 | -0.375 | 0.771 | ALERT | ALERT | False |
| `NEW_LIVE` | -0.679 | -0.279 | 0.800 | ALERT | ALERT | False |

## Verdict

NEW_LIVE (FINBAND+KD+A05) vs OLD_SF_KD held-out score=-0.679 tip_clean=False YTD=ALERT 1y=ALERT. Live Soft-Frozen=[0.6, 0.9].

Repro: `repro/live-stack-rerun-20260909/`
