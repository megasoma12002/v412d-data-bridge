# FIN buy-quality — 2015 / 2020 stress-window backtest

Date: 2026-09-28  
Status: **STRESS_SLICE_DONE** · Soft-Frozen **KEEP** · no live wire  
Parent: Stage B `BUY_QUALITY_HIT` · champion `B_MA120_OR_K9` · seed `SEED_MA120`  
Source NAV: `repro/fin-buy-quality-stageb/outputs/nav_*.csv` (Exact T+1 twin + COOL)

## Windows

| ID | Span | Why |
|---|---|---|
| `2015_calendar` | 2015-01-01 → 2015-12-31 | Full year |
| `2015_summer_crash` | 2015-04-01 → 2015-09-30 | Mid-year selloff (peak≈Apr-28 → trough≈Aug-24) |
| `2020_calendar` | 2020-01-01 → 2020-12-31 | Full year |
| `2020_covid_crash` | 2020-01-15 → 2020-04-30 | COVID peak→trough (peak≈Jan-20 → trough≈Mar-19) |
| `2020_feb_mar` | 2020-02-01 → 2020-03-31 | Acute crash months |

MDD = max drawdown **inside** the window (renormalized to window start).  
`mddΔ` vs CTRL: **positive = shallower drawdown** (better).

## Results vs `CTRL_BASE`

### 2015

| Book | calendar ret | calendar MDD | summer MDD | vs CTRL summer mddΔ |
|---|---:|---:|---:|---:|
| CTRL_BASE | −1.66% | −10.02% | −9.42% | — |
| SEED_MA120 | −1.89% | −9.59% | −9.59% | −0.17pp |
| **B_MA120_OR_K9** | −1.87% | −9.60% | −9.60% | −0.18pp |
| B_MA180 | −2.47% | −9.47% | −9.47% | −0.05pp |

**Read:** 2015 stress is **near-flat vs CTRL** — no material MDD damage; also no big MDD win. Summer trough dates align (≈2015-08-24).

### 2020 (COVID)

| Book | calendar ret | covid MDD | feb–mar MDD | vs CTRL covid mddΔ | vs CTRL feb–mar mddΔ |
|---|---:|---:|---:|---:|---:|
| CTRL_BASE | +5.47% | −14.11% | −13.30% | — | — |
| SEED_MA120 | +4.94% | −13.22% | −11.72% | **+0.89pp** | **+1.58pp** |
| **B_MA120_OR_K9** | **+5.79%** | **−12.06%** | **−10.92%** | **+2.05pp** | **+2.38pp** |
| B_MA180 | +5.25% | −13.79% | −12.32% | +0.32pp | +0.98pp |

**Read:** Champion **helps in 2020 crash** — shallower MDD (~2pp) and better acute feb–mar path; calendar return also slightly above CTRL.

## Binding takeaway

1. **2020 COVID:** `B_MA120_OR_K9` **passes** stress check vs CTRL (MDD↑ ~+2pp, ret not worse).  
2. **2015 summer:** **neutral** (within ~0.2pp MDD of CTRL) — not a failure, not a claim of crisis alpha.  
3. Does **not** by itself authorize live wire; reinforces Stage B paper observe case.  
4. Ignore `*_peak_to_yearend` for 2020 as a crash metric (CTRL peak lands late-Nov → trivial late-year MDD).

## Reproduce

```bash
# uses existing Stage B nav CSVs
PYTHONPATH=scripts python3 - <<'PY'
# see research/ops/FIN_BUY_QUALITY_STRESS_2015_2020.md procedure /
# artifact: /opt/cursor/artifacts/fin_buy_quality_stress_2015_2020.csv
PY
```

CSV: `repro/fin-buy-quality-stageb/reports/FIN_BUY_QUALITY_STRESS_2015_2020.csv`  
Label: `FIN_BUY_QUALITY_STRESS_2015_2020_2026-09-28__CHAMP_COVID_HELP_2015_FLAT`
