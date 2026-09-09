# FIN post-exdiv autumn low — paper probe

Generated: `2026-09-09T09:37:32.465258+00:00`
Status: **PAPER_PROBE** · Soft-Frozen **KEEP** · live wire **false** · live **KD_OPT untouched**

## Season

- Window: **10/20 – 12/10** (after cash-ex)
- KD: Yahoo **K9/D9**

## Pattern A — post-ex local low in autumn?

Window trading days **T+1..T+100** close argmin → share in Oct20–Dec10:
**25.8%** (baseline ~33.9%, lift ×0.76) — **not** a strong autumn-local-low cluster

Median dist ex→low: **31.5** sessions

## Pattern B — autumn Yahoo K9 → +40d hold

| rule | hit rate | med ret | vs random med | near season low |
|---|---:|---:|---:|---:|
| `Klt20` | 69.4% | 2.85% | +0.89pp | 62.8% |
| `Klt25` | 75.8% | 2.27% | +0.90pp | 63.8% |
| `Klt30` | 83.9% | 2.40% | +1.05pp | 57.7% |

### Primary line: `Klt25`

- Hits: **47** / 62 eligible post-ex seasons
- Median +40d ret: **2.27%**
- Edge vs random same window: **+0.90 pp**

## Implications

- Distinct from live **KD_OPT** (Apr–May pre-ex)
- Event-study edge is modest; sleeve NAV follow-up: `FIN_POST_EXDIV_AUTUMN_NAV.md`
  - held-out **+0.422** vs EQUAL · tip **PASS** · **below** live KD_OPT (**+0.65**)

## Hard rules

- Soft-Frozen KEEP · no live wire · no cutover from this probe
- Does not change live `KD_OPT`

Repro: `repro/fin-post-exdiv-autumn-probe-20260909/`  
NAV: `research/ops/FIN_POST_EXDIV_AUTUMN_NAV.md`
