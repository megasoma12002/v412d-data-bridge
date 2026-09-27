# FIN tip / sealed fill quality — Stage A Screen

Generated: `2026-09-26T15:22:35Z`
Status: **`FIN_BOTH_WEAK`** · Soft-Frozen KEEP · **no live wire** · `ohlc_basis=adj_close_scaled` · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

## Gaps vs gates

| gap | pp | gate ≥0.5 |
|---|---:|---|
| tip FIN − tip TEL ±5d | 1.8022 | Y |
| sealed FIN − sealed TEL ±5d | 0.5395 | Y |
| tip FIN − sealed FIN ±5d | 1.8963 | Y (unique-tip ≥0.5) |

## Tip window

Fills **96** · `2026-08-25` → `2026-09-16`

| sleeve_side | n | ±5 mean | ±5 med | ±21 mean | T+1 |
|---|---:|---:|---:|---:|---:|
| `ALL_ALL` | 96 | 3.7887 | 3.115 | 7.7602 | 1.1543 |
| `FIN_ALL` | 48 | 4.6479 | 4.1885 | 9.036 | 1.6175 |
| `FIN_BUY` | 48 | 4.6479 | 4.1885 | 9.036 | 1.6175 |
| `TEL_ALL` | 36 | 2.8457 | 2.6486 | 5.704 | 0.6366 |
| `0050_ALL` | 12 | 3.1807 | 3.5429 | 8.8256 | 0.8541 |

### Tip FIN mechanism slices

KD off−in Δn5 **None** · CLIP−not Δn5 **4.7391** · COOL on−off Δn5 **None**

| slice | n | ±5 mean | T+1 |
|---|---:|---:|---:|
| `all` | 48 | 4.6479 | 1.6175 |
| `kd_off` | 48 | 4.6479 | 1.6175 |
| `clip_fin_hi` | 24 | 7.0175 | 2.1319 |
| `not_clip_fin_hi` | 24 | 2.2784 | 1.1032 |
| `cool_off` | 48 | 4.6479 | 1.6175 |
| `buy` | 48 | 4.6479 | 1.6175 |

| mechanism | n |
|---|---:|
| `T1_ALWAYS` | 48 |
| `T1_DRAG` | 48 |
| `KD_OFFSEASON` | 48 |
| `CLIP_FIN_HI` | 24 |

## Sealed 2023+ (FUSE+COOL twin)

Fills **1667** · `2023-01-10` → `2026-09-07`

| sleeve_side | n | ±5 mean | ±5 med | ±21 mean | T+1 |
|---|---:|---:|---:|---:|---:|
| `ALL_ALL` | 1667 | 2.7087 | 2.2711 | 5.3618 | 0.8466 |
| `FIN_ALL` | 806 | 2.7516 | 2.3832 | 5.1836 | 0.9341 |
| `FIN_BUY` | 447 | 2.768 | 2.4994 | 5.1523 | 1.0396 |
| `FIN_SELL` | 359 | 2.7311 | 2.2629 | 5.2225 | 0.8028 |
| `TEL_ALL` | 645 | 2.2121 | 1.8366 | 4.2172 | 0.7182 |
| `0050_ALL` | 216 | 4.0312 | 3.6342 | 9.4446 | 0.9037 |

### Sealed FIN mechanism slices

KD off−in Δn5 **-0.4373** · CLIP−not Δn5 **None** · COOL on−off Δn5 **-0.0285**

| slice | n | ±5 mean | T+1 |
|---|---:|---:|---:|
| `all` | 806 | 2.7516 | 0.9341 |
| `kd_in` | 72 | 3.1498 | 0.9962 |
| `kd_off` | 734 | 2.7125 | 0.9281 |
| `not_clip_fin_hi` | 806 | 2.7516 | 0.9341 |
| `cool_on` | 209 | 2.7305 | 0.8049 |
| `cool_off` | 597 | 2.759 | 0.9794 |
| `buy` | 447 | 2.768 | 1.0396 |
| `sell` | 359 | 2.7311 | 0.8028 |

## Tip FIN weak-bucket concentration

Fills with n5 > FIN median (4.1885%): n=24 · top non-T1 tag `KD_OFFSEASON` 24 (100%) · conc_flag=Y

### Read

Verdict **`FIN_BOTH_WEAK`**: both tip and sealed FIN ≥0.50pp worse than TEL peers.

Repro: `PYTHONPATH=scripts python3 scripts/fin_tip_sealed_fill_stagea.py`

Label: `FIN_TIP_SEALED_FILL_STAGEA_SCREEN_2026-09-26__FIN_BOTH_WEAK`
