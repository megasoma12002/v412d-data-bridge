# FIN signal improve Stage A — Screen

Generated: `2026-09-26T15:47:26Z`
Status: **`NAV_ONLY`** · Soft-Frozen KEEP · Exact T+1 KEEP · **no live wire** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

## Track verdicts

| track | verdict |
|---|---|
| `C_CLIP` | `C_CLIP_NO_LIFT` |
| `D_COOL` | `D_COOL_NO_LIFT` |
| `B_KD` | `B_KD_NO_LIFT` |

## Base (sealed FIN BUY fill)

n=447 · ±5d mean **2.768%** · FIN−TEL **0.5559pp**

## Challengers

| id | track | fill Δpp | fill gate | MDD Δpp | CAGR gb | nav gate | HIT |
|---|---|---:|:---:|---:|---:|:---:|:---:|
| `C_FIN_HI_075` | `C_CLIP` | 0.1171 | n | -0.0929 | -0.1003 | Y | n |
| `C_FIN_HI_090` | `C_CLIP` | -0.2225 | n | -0.0014 | 0.178 | Y | n |
| `D_COOL_OFF` | `D_COOL` | 0.0787 | n | -7.5284 | -0.7952 | n | n |
| `D_COOL_FLOOR_070` | `D_COOL` | 0.0936 | n | -3.1583 | 0.0218 | n | n |
| `B_KD_BUYOK_ALWAYS` | `B_KD` | 0.0545 | n | -0.0308 | 0.0509 | Y | n |
| `B_KD_OFFSEASON_NO_BUY` | `B_KD` | -0.4264 | n | 3.4113 | 4.0164 | n | n |

### Read

NAV near-flat/better; fill gate not cleared.

Repro: `PYTHONPATH=scripts python3 scripts/fin_signal_clip_cool_kd_stagea.py`

Label: `FIN_SIGNAL_CLIP_COOL_KD_STAGEA_SCREEN_20260926__NAV_ONLY`
