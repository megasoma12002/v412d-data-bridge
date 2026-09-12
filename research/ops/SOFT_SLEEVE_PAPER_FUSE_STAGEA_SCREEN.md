# Soft × Sleeve Paper Fuse Stage A Screen

Generated: `2026-09-12T14:01:46.832212+00:00` · asof **2026-09-11**
Verdict: **`FUSE_PROMOTE_SHAPED_BEATS_BOTH`** · books **8**
Live wire: **false** · ops auto-fuse: **false** · observe swap: **false**

## Question

Does any Soft×Sleeve joint-actuator fuse book promote-shaped-beat Soft-only and Sleeve-only on `LIVE_STACK`?

## Summary

- Soft-only `SOFT_ONLY_ON_STACK` held **0.101** (Soft observe softs `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` on stack)
- Sleeve-only `SLEEVE_ONLY` (`SLEEVE_RSI14_LT30_a0225`) held **0.099**
- Better independent held **0.101**
- Fuse promote-shaped: **2** → `['FUSE_ADDITIVE', 'FUSE_HALF_ALPHA']`
- Fuse beats both independents: **1** → `['FUSE_ADDITIVE']`

## Books

| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD |
|---|---|---|---|:---:|:---:|---:|---:|---:|---:|
| `FUSE_ADDITIVE` | fuse | PASS | PASS | Y | Y | 0.164 | 0.180 | 18.36% | -21.54% |
| `SOFT_ONLY_ON_STACK` | soft_only | PASS | PASS | Y | Y | 0.101 | 0.101 | 18.39% | -21.62% |
| `NAV_BLEND_50` | diagnostic | PASS | PASS | Y | Y | 0.100 | 0.103 | 18.39% | -21.62% |
| `SLEEVE_ONLY` | sleeve_only | PASS | PASS | Y | Y | 0.099 | 0.104 | 18.38% | -21.62% |
| `FUSE_HALF_ALPHA` | fuse | PASS | PASS | Y | Y | 0.096 | 0.117 | 18.35% | -21.60% |
| `LIVE_STACK` | base | PASS | PASS | Y | N | 0.000 | 0.000 | 18.39% | -21.72% |
| `FUSE_SLEEVE_GATE_SOFT` | fuse | PASS | PASS | Y | N | 0.000 | 0.000 | 18.39% | -21.72% |
| `FUSE_SOFT_GATE_SLEEVE` | fuse | PASS | PASS | N | N | -0.101 | -0.077 | 18.44% | -21.80% |

## Reading

- `FUSE_*` books apply Soft observe softs and/or Sleeve observe tilt together on `LIVE_STACK`.
- `NAV_BLEND_50` is post-hoc diagnostic only (not a tradable joint book).
- Operating Soft∥Sleeve dual observe and Gate H auto-fuse ban are unchanged.

## Non-actions

- No Soft×Sleeve auto-fuse on operating path (Gate H stays)
- No Soft or Sleeve observe swap
- No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire
- No joint ACCEPT / cutover unlock
- No Soft-buy MLP deepen

## Label

`SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN_2026-09-11__FUSE_PROMOTE_SHAPED_BEATS_BOTH`
