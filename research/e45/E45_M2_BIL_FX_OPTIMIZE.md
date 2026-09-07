# E45 M2 BIL_FX Optimize Paper

- Generated: `2026-09-06T17:06:01.073942+00:00`
- Freeze: `research/e45/E45_M2_BIL_FX_OPTIMIZE_V0_FROZEN.md`
- Repro: `repro/e45-m2-bil-fx-optimize/`
- Claim status: `RETIRED_HISTORICAL_NARRATIVE`

## A) Path-dependent FX friction (C50 mid-marked)

Method: `|Δw_DEF| · h_t` with `h_t = (spot_sell − spot_buy) / (2 · usdtwd_mid)` applied to mid-marked early-stack returns.

- Mean `h_t`: `0.0016396159563049383`
- Held giveback vs mid @ FXPATH: `0.6169627595572491` pp
- Material (≥0.10 pp vs mid)? **`True`**
- FXPATH §2: `True` · held score `+0.88`
- MID C50 §2: `True` · held score `+1.24`

| Book | held score | giveback pp | MDD improve pp | §2 |
|---|---:|---:|---:|---|
| `M2_RELOC_BIL_FX_C50` | +1.24 | +3.43 | +2.96 | Y |
| `M2_RELOC_BIL_FX_C50_FXPATH` | +0.88 | +4.05 | +2.90 | Y |
| `M2_RELOC_BIL_FX_C50_FXH10` | +1.02 | +3.81 | +2.92 | Y |
| `M2_RELOC_BIL_FX_C50_FXH25` | +0.68 | +4.38 | +2.87 | Y |
| `M2_RELOC_BIL_FX_C50_FXH50` | +0.07 | +5.32 | +2.73 | N |

## B) TWD CBC cash twin vs BIL_FX / cash0 / 00720B

CBC rediscount is a **policy-rate cash carry proxy** (not retail deposit / MM).

| Book | held score | giveback pp | §2 |
|---|---:|---:|---|
| `M2_RELOC_BIL_FX_C50` | +1.24 | +3.43 | Y |
| `M2_RELOC_TWD_CASH_CBC_C50` | +0.95 | +3.55 | Y |
| `M2_RELOC_TWD_CASH_CBC_C75` | +2.30 | +5.59 | Y |
| `M2_RELOC_TWD_CASH0_C50` | +0.80 | +3.80 | Y |
| `M2_RELOC_TWD_720B_C50` | -3.62 | +4.31 | N |

## C) Cut × intensity-cap grid (BIL_FX mid)

Cuts `[0.35, 0.4, 0.45, 0.5, 0.55, 0.6]` @ κ=1; κ `[0.6, 0.8, 1.0]` @ c=0.50.

**Preferred among cut grid:** `M2_RELOC_BIL_FX_C35` · held score `+1.51` · giveback `+2.23` · §2 `Y`

| Book | cut | κ | held score | giveback pp | §2 |
|---|---:|---:|---:|---:|---|
| `M2_RELOC_BIL_FX_C35` | 0.35 | 1.0 | +1.51 | +2.23 | Y |
| `M2_RELOC_BIL_FX_C40` | 0.4 | 1.0 | +1.53 | +2.60 | Y |
| `M2_RELOC_BIL_FX_C45` | 0.45 | 1.0 | +1.43 | +3.00 | Y |
| `M2_RELOC_BIL_FX_C50_K60` | 0.5 | 0.6 | +1.13 | +3.36 | Y |
| `M2_RELOC_BIL_FX_C50_K80` | 0.5 | 0.8 | +1.24 | +3.43 | Y |
| `M2_RELOC_BIL_FX_C50` | 0.5 | 1.0 | +1.24 | +3.43 | Y |
| `M2_RELOC_BIL_FX_C55` | 0.55 | 1.0 | +1.57 | +3.82 | Y |
| `M2_RELOC_BIL_FX_C60` | 0.6 | 1.0 | +1.81 | +4.27 | Y |

## D) Observe OPEN (user-authorized)

- Variant: **`M2_RELOC_BIL_FX_C50`**
- Authorization: human 「請全做」 (2026-09-06)
- Status: **OPERATING_OBSERVE** (dual-ledger + month-end monitor)
- **NOT** live DEFAULT; stitch still **FORBIDDEN**; C75 remains ballot-gated

## Hard non-actions

- Soft-Frozen FIN clip [0.50, 0.95] KEEP
- Live DEFAULT `E22_v2s_tw` KEEP
- Live E45 stitch FORBIDDEN
- No invent MDD replacement
- CBC rediscount ≠ retail TWD cash

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_optimize_paper.py
```

