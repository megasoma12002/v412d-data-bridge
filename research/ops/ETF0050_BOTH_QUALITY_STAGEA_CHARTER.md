# ETF 0050 both-quality Stage A — buy×sell sleeve filters (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · β densify clip **KEEP** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Prior 0050 tracks (do **not** reopen same knob):
- β densify → **`BETA_0050_HIT` → LIVE clip** · Stage B `HELD_FLAT_TIP_FAIL`
- Asymm Bull densify → **`CAGR_SOFT`**
- BUY fill / slew → **`METRIC_ARTIFACT_ONLY`**
- Ex-calendar → **`NEAR_NO_BEAT` / STOP**

Human intent (normalized):

```
OPEN Stage A charter: 0050 買賣品質過濾 · 加減碼時機 · MDD持平/改善 + CAGR↑ · 勝率診斷 · KEEP clip/SELL_a75 · paper only
```

Label: `ETF0050_BOTH_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why this track

0050 is a **single-name sleeve** (no within-sleeve `buy_ok` like FIN KD_OPT). Live mass densify and BUY slew are exhausted. Remaining lever: **when** Soft-Frozen+FUSE+COOL may **increase or decrease** the 0050 target — quality-gate the Δw, not the clip bounds.

Belief: skip low-quality 0050 adds and/or weak 0050 cuts → held CAGR↑ + MDD flat/↑ (+ sleeve WR↑).  
Risk: freeze too many ups → starve β sleeve CAGR; freeze downs → hold losers → MDD/tip fail; or cancel buy×sell edges.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen live clips `E[0.00,0.50]` (β densify) | **KEEP** — no clip densify this Stage |
| Exact T+1 · COOL_c8 · FUSE · live **SELL_a75** | **KEEP** |
| BUY slew / batch-in fill (`ETF0050_BUY_FILL`) | **CLOSED** — do not reopen |
| Asymm Bull densify / always-on E hi push | **CLOSED** — do not reopen |
| Ex-calendar timing | **STOP** — do not reopen |
| FINCAP50 / FIN both-quality observe | **out of scope** (other sleeves) |
| Live wire / broker / tip rewrite | **forbidden** this Stage |

## Mechanism (paper overlay)

On `BASE_LIVE_FUSE_COOL` daily sleeve targets `w_t` (Financial / Telecom / **0050**):

1. Compute intended Δ = `w_t["0050"] − w_{t−1}["0050"]`.  
2. **Buy gate** (when Δ &gt; 0): if `etf_buy_ok` fails → set 0050 to prior; redistribute residual mass to FIN+TEL **pro-rata** (simplex ∩ Soft-Frozen box).  
3. **Sell gate** (when Δ &lt; 0): if `etf_sell_ok` fails → set 0050 to prior; take residual from FIN+TEL pro-rata.  
4. Indicators from **0050** adj close + live cool exposure (not FIN/TEL names).

`etf_buy_ok` / `etf_sell_ok` default **True** on `CTRL_BASE`.

## Question

Does a finite buy×sell quality grid produce ≥1 book with:

1. held **CAGR↑** ≥ **+0.15pp** where ↑ = **chal − base**  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & trailing-1y MDD↑ ≥ **0**  
4. Diagnostic (HIT bar, either side): 0050 BUY WR↑ H=21 ≥ **+0.5pp** **or** 0050 SELL WR↑ (fwd ret &lt; 0) ≥ **+0.5pp**

## Metric sign (binding)

- Helpers’ `cagr_delta_pp(base, chal)` = giveback (**BASE − CHAL**).  
- Report `held_cagr_lift_pp = −cagr_delta_pp(...)` and gate on **lift**.  
- Do not print giveback as CAGR↑.

## Stage A grid (finite ≤14 — do not expand after peek)

| ID | Buy (`etf_buy_ok` when Δ&gt;0) | Sell (`etf_sell_ok` when Δ&lt;0) |
|---|---|---|
| `CTRL_BASE` | always | always |
| `BUY_BELOW_MA120` | AND `close < MA120` | — |
| `BUY_ABOVE_MA60` | AND `close > MA60` | — |
| `BUY_RET5_POS` | AND RET5 &gt; 0 | — |
| `BUY_NOT_COOL` | AND cool≈1 **blocked** (no add while defending) | — |
| `SELL_ABOVE_MA60` | — | AND `close > MA60` |
| `SELL_RET5_NEG` | — | AND RET5 &lt; 0 |
| `SELL_RSI14_GT70` | — | AND RSI14 &gt; 70 |
| `SELL_COOL1_ONLY` | — | AND cool≈1 (cut mainly while defending) |
| `BOTH_MA120_x_MA60` | BELOW_MA120 | ABOVE_MA60 |
| `BOTH_RET5_x_RET5` | RET5&gt;0 | RET5&lt;0 |
| `BOTH_NOTCOOL_x_COOL` | NOT_COOL add | COOL1_ONLY cut |
| `BOTH_MA60TREND_x_RSI` | ABOVE_MA60 | RSI14&gt;70 |
| `BUY_RET5_NEG_CTRL` | AND RET5 &lt; 0 (**NEG** control) | — |

## Verdicts

| Verdict | Meaning |
|---|---|
| `ETF_BOTH_QUALITY_HIT` | ≥1 **BOTH_*** (or joint-clearing single) clears all HIT gates |
| `WIN_SOFT` | economic (1–3) clear; WR short |
| `CAGR_SOFT` | MDD+tip clear; CAGR short |
| `SINGLE_SIDE_ONLY` | only BUY_* or SELL_* clears economic; joint fails |
| `MDD_BLOCK` / `TIP_BLOCK` | structural fail |
| `NO_EDGE` | no legal challenger clears economic gates |

Even HIT → **paper observe ballot only**; Soft-Frozen / live wire = separate ACCEPT.

## Non-actions

- Soft-Frozen clip flip / Exact T+1 / tip rewrite  
- Re-open β densify · asymm densify · BUY slew · ex-calendar  
- Lower / remove live `SELL_a75`  
- FIN / TEL within-sleeve retune  
- Live wire / broker / COOL retune  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/etf0050_both_quality_stagea.py
```

Artifacts: `research/ops/ETF0050_BOTH_QUALITY_STAGEA_*` · `repro/etf0050-both-quality-stagea/`
