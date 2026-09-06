# E45 M2 BIL_FX improve pack (FX sensitivity + TWD twin)

Generated: `2026-09-06T16:31:55.356414+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**.
Observe wiring: **`AWAITING_HUMAN_ACCEPT`** — see `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`.
Freeze: `research/e45/E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md`

## Non-claims

- No Soft-Frozen / DEFAULT / stitch change
- No observe ACCEPT / OPEN cast
- Haircut / spot marks are research FX friction proxies (not bank quotes)
- `TWD_CASH0` = flat 0% bound; `00720B` = short-bond ETF — neither is pure bank cash
- Claimed MDD: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement

## ① FX mark sensitivity (`RELOC_BIL_FX`)

| Book | §2 | Held score | COVID-ex score | Giveback pp | Years |
|---|---|---:|---:|---:|---|
| `M2_RELOC_BIL_FX_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_MID_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_SPOT_BUY_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_SPOT_SELL_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_H5_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_H10_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_H25_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_H50_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_MID_C75` | PASS | +2.67 | +3.41 | +5.46 | 2015,2018,2020,2022 |
| `M2_RELOC_BIL_FX_H25_C75` | PASS | +2.67 | +3.41 | +5.46 | 2015,2018,2020,2022 |

**Informational gate (freeze):** SPOT_BUY C50 §2 = **PASS**; MID_H25 C50 §2 = **PASS**.
FX §2 PASS books: `M2_RELOC_BIL_FX_MID_C50, M2_RELOC_BIL_FX_MID_C75, M2_RELOC_BIL_FX_SPOT_BUY_C50, M2_RELOC_BIL_FX_SPOT_SELL_C50, M2_RELOC_BIL_FX_H5_C50, M2_RELOC_BIL_FX_H10_C50, M2_RELOC_BIL_FX_H25_C50, M2_RELOC_BIL_FX_H50_C50, M2_RELOC_BIL_FX_H25_C75, M2_RELOC_BIL_FX_C50`.

## Method note — FX haircut return invariance

Under the freeze algebra, constant proportional FX haircuts (`MID_H5`…`MID_H50`)
markdown the **level** series by a fixed factor. That leaves daily **returns** unchanged,
so Exact-T+1 NAV paths (and §2 scores) are **identical** to `MID` by construction.
`SPOT_BUY` / `SPOT_SELL` are nearly return-invariant here because the spot/mid ratio is
almost constant over the sample. Gates still **PASS**, but this pack does **not** measure
path-dependent FX spread / slippage — only mark-level honesty vs the mid baseline.

## ② TWD twin vs BIL_FX MID

| Book | §2 | Held score | COVID-ex score | Giveback pp | Years |
|---|---|---:|---:|---:|---|
| `M2_RELOC_BIL_FX_MID_C50` | PASS | +1.24 | +3.20 | +3.43 | 2015,2018,2020,2022 |
| `M2_RELOC_TWD_720B_C50` | FAIL | -3.62 | -0.57 | +4.31 | 2015,2018,2022 |
| `M2_RELOC_TWD_720B_C75` | FAIL | -4.56 | -2.26 | +6.62 | 2015,2018,2022 |
| `M2_RELOC_TWD_CASH0_C50` | PASS | +0.80 | +1.56 | +3.80 | 2015,2018,2020,2022 |
| `M2_SHRINK_C50` | FAIL | +2.35 | -0.70 | +6.00 | 2015,2018,2020,2022 |
| `M2_RELOC_TEL_C50` | PASS | +0.48 | +0.16 | +2.26 | 2015,2018,2020,2022 |

TWD twin §2 PASS: `M2_RELOC_TWD_CASH0_C50`.

## ③ Observe OPEN prep

Status remains **AWAITING_HUMAN_ACCEPT** (ballot still DRAFT).
Prep doc: `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`.
Scripts: `scripts/e45_m2_bil_fx_dual_paper_ledgers.py`, `scripts/e45_m2_bil_fx_month_end_monitor.py`.

## Held-out deltas @1x (all books)

| Book | Kind | MDD dpp | Giveback | Score | COVID-ex | Years |
|---|---|---:|---:|---:|---:|---|
| M2_RELOC_BIL_FX_MID_C75 | fx_mid | +5.40 | +5.46 | +2.67 | +3.41 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_H25_C75 | fx_h25 | +5.40 | +5.46 | +2.67 | +3.41 | 2015,2018,2020,2022 |
| M2_SHRINK_C50 | m2_shrink | +5.35 | +6.00 | +2.35 | -0.70 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_SPOT_BUY_C50 | fx_spot_buy | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_H5_C50 | fx_h5 | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_MID_C50 | fx_mid | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_C50 | fx_mid_alias | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_H25_C50 | fx_h25 | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_H10_C50 | fx_h10 | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_H50_C50 | fx_h50 | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_SPOT_SELL_C50 | fx_spot_sell | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_TWD_CASH0_C50 | twd_cash0 | +2.70 | +3.80 | +0.80 | +1.56 | 2015,2018,2020,2022 |
| M2_RELOC_TEL_C50 | m2_reloc_tel | +1.61 | +2.26 | +0.48 | +0.16 | 2015,2018,2020,2022 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | +0.91 | +1.25 | +0.29 | -2.41 | 2020 |
| BLEND_E45_A05 | ref_e45 | +0.70 | +0.96 | +0.22 | -2.05 | 2020 |
| BASE_E16_E18_E22_v2s | ref | +0.00 | +0.00 | +0.00 | +0.00 | — |
| M2_RELOC_TWD_720B_C50 | twd_720b | -1.47 | +4.31 | -3.62 | -0.57 | 2015,2018,2022 |
| M2_RELOC_TWD_720B_C75 | twd_720b | -1.25 | +6.62 | -4.56 | -2.26 | 2015,2018,2022 |

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN
- Claimed MDD: `RETIRED_HISTORICAL_NARRATIVE`
- Do not add to `ops_month_end_paper_pack.py` until human ACCEPT OPEN

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_improve_paper.py
```

Repro: `repro/e45-m2-bil-fx-improve/` · Market: `forward/e21/live_market.csv`
Inputs sha256: BIL=`3129d20a1717…`, USDTWD=`e8d7b9db8352…`, 00720B=`a3243b7409b4…`

