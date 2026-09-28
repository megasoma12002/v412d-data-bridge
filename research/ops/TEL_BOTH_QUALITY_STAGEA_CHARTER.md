# TEL both-quality Stage A — within-sleeve buy×sell (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · FIN **KD_OPT** + `SELL_a75` **KEEP** · TEL live **T3_COOL_INV_VOL20** **KEEP** · no live wire  

Parents:
- TEL within-sleeve Stage A → live cutover `T3_COOL_INV_VOL20` (cool-gated INV_VOL20 · equal off-defense)
- FIN both-quality Stage A `WIN_SOFT` / Stage B HIT (FIN path locked here — do not rechallenge FIN)

Human intent (normalized):

```
OPEN Stage A: TEL 買賣側聯優 · 有限 buy×sell grid on T3_COOL_INV_VOL20 twin · MDD持平/改善 + CAGR↑ · 勝率兼顧 · KEEP Soft-Frozen / FIN KD_OPT / SELL_a75 · paper only · no live wire
```

Label: `TEL_BOTH_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Live twin (CTRL_BASE)

| Sleeve | Path |
|---|---|
| Soft-Frozen 3-sleeve clips | **KEEP** |
| FIN | `FIN_PRE_EXDIV_KD` + KD_OPT soft-assist + **SELL_a75** |
| TEL | `TEL_RS_SOFT_TILT` + cool-gated `INV_VOL20` (`T3_COOL_INV_VOL20`) · equal when `cool_exposure=1` |
| COOL | `COOL_c8` from offense NAV |

TEL codes: `2412` · `3045` · `4904`. Catalog + WR diagnostics on TEL only.

## Challenge surface

FIN path **locked**. Only TEL overlays via:
- `tel_buy_ok` (hard buy filter; uses `TEL_RS_SOFT_TILT_EXDIV` when set so buy_ok is honored)
- `tel_sell_ok` (hard sell gate)
- `tel_sell_scores` (soft dampen from equal sell base)

## Gates (HIT → `TEL_QUALITY_HIT`)

1. held **CAGR↑** ≥ **+0.15pp** (**chal − base**)  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & 1y MDD↑ ≥ **0**  
4. TEL BUY WR↑ H=21 ≥ **+0.5pp** **or** TEL SELL WR↑ (fwd&lt;0) ≥ **+0.5pp**

Soft path `WIN_SOFT`: economic (1–3) clear; WR short.

## Grid (finite ≤12)

| ID | Buy overlay | Sell overlay |
|---|---|---|
| `CTRL_BASE` | — (live twin) | — |
| `BUY_MA60` | hard `BELOW_MA60` | — |
| `BUY_MA120` | hard `BELOW_MA120` | — |
| `BUY_OR_K9` | hard `BELOW_MA120`∨`K9_LT30` | — |
| `BUY_RSI14_LT40` | hard RSI14&lt;40 | — |
| `SELL_HARD_MA60` | — | hard `NOT_BELOW_MA60` |
| `SELL_HARD_MA120` | — | hard `NOT_BELOW_MA120` |
| `SELL_DAMP_MA60_d50` | — | damp×0.50 when below MA60 |
| `BOTH_MA60_x_HARD60` | `BELOW_MA60` | hard `NOT_BELOW_MA60` |
| `BOTH_OR_K9_x_HARD60` | MA120∨K9 | hard `NOT_BELOW_MA60` |
| `BOTH_MA120_x_HARD120` | `BELOW_MA120` | hard `NOT_BELOW_MA120` |
| `BOTH_OR_K9_x_HARD120` | MA120∨K9 | hard `NOT_BELOW_MA120` |

## Verdicts

| Verdict | Meaning |
|---|---|
| `TEL_QUALITY_HIT` | ≥1 challenger clears HIT |
| `WIN_SOFT` | ≥1 challenger clears economic; WR short |
| `MDD_BLOCK` | CAGR↑ ok · MDD/tip/band fail |
| `NO_EDGE` | no CAGR↑ |

Even HIT → **ballot only**; no live wire from Stage A. Screen fills on run.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/tel_both_quality_stagea.py
```

Artifacts: `research/ops/TEL_BOTH_QUALITY_STAGEA_*` · `repro/tel-both-quality-stagea/`
