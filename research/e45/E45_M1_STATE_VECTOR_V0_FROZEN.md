# E45 M1 — Frozen State Vector v0 (BEFORE any sealed metrics)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER SCREEN** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_NEW_MECHANISM_CHARTER.md` (M1 sensor stage)  
Claimed MDD −13.16%: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Honesty bound

Repo has **no** TW rates / TWD FX / credit / official PE series.  
v0 is therefore an **equity/TAIEX-derived proxy sensor**, not a true macro sensor.  
That limitation is intentional and must appear in every M1 scoreboard.

If v0 fails §2, the correct next step is **new data ingest** or **M2 DEF sleeve**, not densifying E45 α.

## Universe / calendar

- Prices: `forward/e21/live_market.csv` (`close`), codes = early-stack `ALL` + `TAIEX`
- Optional crash flag: `forward/e10s2/e10s2_taiex.csv` → `shock_combined`
- Feature time `t` uses data available at close `t`; exposure applied with **1 trading-day lag** (Exact T+1 honesty)

## Feature definitions (frozen)

Let `P_i,t` = close of name `i` on day `t`.  
`TAIEX_t` = TAIEX close.  
`FIN_t` = equal-weight mean of Financial sleeve closes `{2880,2886,2892,5880}`.

| ID | Formula | Risk map → `[0,1]` |
|---|---|---|
| `R_DD` | Drawdown from 252d peak: `1 - TAIEX_t / max_{t-251..t} TAIEX` | `clip(R_DD / 0.20, 0, 1)` |
| `R_VOL` | `vol20 = std(logret_TAIEX, 20)`; percentile of `vol20` vs trailing 252d | `percentile ∈ [0,1]` (NaN→0) |
| `R_BREADTH` | Fraction of `ALL` names with `P_i,t > SMA_120(P_i)` | `1 - breadth` |
| `R_FINREL` | `z = (x - mean_60(x)) / std_60(x)` where `x = log(FIN/TAIEX)` | `clip(max(0, -z) / 2, 0, 1)` |
| `R_SHOCK` | `shock_combined` from e10s2 aligned on date (False if missing) | `1` if shock else `0` |

Equal-weight state intensity:

```
s_t = mean(R_DD, R_VOL, R_BREADTH, R_FINREL, R_SHOCK)   # skip NaN components
s_t = clip(s_t, 0, 1)
```

## Exposure map (frozen)

Whole-book challengers (primary):

```
exposure_t = 1 - c * s_{t-1}     # 1-day lag
c ∈ {0.25, 0.50, 0.75}
```

Book IDs:

| Book | Rule |
|---|---|
| `M1_EQW_C25` | `c=0.25`, whole-book |
| `M1_EQW_C50` | `c=0.50`, whole-book |
| `M1_EQW_C75` | `c=0.75`, whole-book |
| `M1_EQW_C50_FIN` | `c=0.50`, scale **Financial sleeve only** |

## References (always run)

- `BASE_E16_E18_E22_v2s`
- `BLEND_E45_A05`
- `SLEEVE_FIN_ONLY_A10` (observe OPERATING id — reference only)

## Explicit non-actions

- Do **not** call `e45.compute_exposure(..., E3_VOLTARGET_WINNER)` as the M1 primary sensor (ablation/reference only via `BLEND_E45_A05`)
- Do **not** retune Soft-Frozen / stitch / HIGH_BETA
- Do **not** change these formulas after seeing sealed scores (amendment = new `v1` freeze doc)

## Qualification (§2 of new-mechanism charter)

Same binding gates: multi-event, held-out score>0, sealed>-1, strict non-COVID multi-event, COVID-ex held-out>0, cost 1× & 2× hold.

## Post-screen note (do not change formulas)

Paper pack `E45_M1_STATE_SIGNAL` ran against this freeze: best M1 held-out is `M1_EQW_C75`, multi-year help includes non-2020, but **COVID-ex held-out score stays negative** → **Section-2 FAIL** (autopsy). Next authorized step remains **M2**, not E45 α densify.

Label: `E45_M1_STATE_VECTOR_V0_FROZEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
