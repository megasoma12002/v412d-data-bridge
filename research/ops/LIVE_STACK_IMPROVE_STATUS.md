# Live stack improvement status (post DROP_E45_A05)

Generated: `2026-09-09T12:52:23.827736+00:00`
Status: **IMPROVED**

## Before → after rollback

| | RETIRED (FINBAND+KD+A05) | CURRENT_LIVE (FINBAND+KD) | Δ |
|---|---:|---:|---:|
| held-out score vs OLD | -0.679 | +0.023 | +0.701 |
| tip YTD / 1y | ALERT / ALERT | PASS / PASS | tip_restored=True |
| full CAGR | 13.56% | 13.92% | +0.36 pp |
| full MDD | -22.05% | -21.72% | MDD↑ +0.329 pp |

## vs pre-big-win Soft-Frozen+KD (`OLD_SF_KD`)

- CURRENT_LIVE: held-out **+0.023**, tip **PASS** (near flat / slight edge).
- RETIRED_FINBAND_A05: held-out **-0.679**, tip ALERT.

## Reading

Dropping E45 A05 restored tip cleanliness and recovered ~0.70 held-out score vs the pre-rollback live stack. Live remains Soft-Frozen FINBAND + KD_OPT with E45 stitch OFF.

Detail: `LIVE_STACK_RERUN.md` · Repro: `repro/live-stack-rerun-20260909/`
