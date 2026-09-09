# FIN pre-exdiv + Yahoo K9/D9 — paper probe

Generated: `2026-09-09T00:08:20.427306+00:00`
Status: **PAPER_PROBE** · Soft-Frozen **KEEP** · live wire **false**

## KD spec (match Yahoo TW chart)

- Labels: **K9 / D9** (RSV lookback **9**)
- `K = ⅔·Kprev + ⅓·RSV` · `D = ⅔·Dprev + ⅓·K` · `J = 3K − 2D`
- **Not** SMA(9)/SMA(9,9)

## Pattern A — local high near cash ex-div

Window `[T-60, T+20]` close argmax → share in **T-10..T-1**:
**69.0%** (baseline ~12.3%, lift ×5.6)

## Pattern B — May15–Jun10 Yahoo K9 → pre-ex high

| rule | hit rate | med ret→pre-ex high | vs random med | local-low OK |
|---|---:|---:|---:|---:|
| `Kle20` | 46.7% | 8.5% | +2.11pp | 35.7% |
| `Klt20` | 46.7% | 8.5% | +2.11pp | 35.7% |
| `Klt25` | 53.3% | 8.0% | +1.62pp | 37.5% |

### Primary observe line: `Klt25`

- Hits: **32** / 60 events
- Median ret to pre-ex high: **8.0%**
- Edge vs random same window: **+1.62pp**

## Implications

- Pre-exdiv high clustering is strong on FIN names — skip-buy on ex-date alone is too late/narrow
- Yahoo K9 seasonal signal has modest edge vs random same-window day; useful as observe probe not live knife
- Next paper option: PRE_EXDIV_T10 reduce/skip buy, optional May–Jun K9<25 add bias — still Soft-Frozen KEEP

## Hard rules

- Soft-Frozen KEEP · no live wire · no cutover from this probe
- Does not replace OPERATING FIN triad (`EQUAL` ∥ `RS_EXDIV` ∥ `MIX_L75`)

Repro: `repro/fin-pre-exdiv-kd-probe-20260909/`
