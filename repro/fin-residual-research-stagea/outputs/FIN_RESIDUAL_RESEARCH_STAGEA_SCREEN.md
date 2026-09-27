# FIN residual research Stage A — Screen

Generated: `2026-09-26T15:56:55Z`
Status: **`SIGNAL_HIT`** · Soft-Frozen KEEP · Exact T+1 KEEP · **no live wire** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

## Track verdicts

| track | verdict |
|---|---|
| `SLEEVE` | `SLEEVE_NO_LIFT` |
| `EXEC` | `EXEC_NO_LIFT` |
| `WITHIN` | `WITHIN_FILL_ONLY` |
| `REBAL` | `REBAL_HIT` |
| `CLOSE` | `CLOSE_NOT_YET` |

## Base (sealed FIN BUY fill)

n=447 · ±5d mean **2.768%** · FIN−TEL **0.5559pp**

## Challengers

| id | track | fill Δpp | fill gate | MDD Δpp | CAGR gb | nav gate | HIT |
|---|---|---:|:---:|---:|---:|:---:|:---:|
| `S_ALPHA_0` | `SLEEVE` | 0.016 | n | -0.0282 | -0.0473 | Y | n |
| `S_TEL_PRE_EXDIV_KD` | `SLEEVE` | 0.0112 | n | 0.0865 | -0.1458 | Y | n |
| `E_COST_0` | `EXEC` | 0.0137 | n | 0.4243 | -1.4682 | Y | n |
| `E_COST_2` | `EXEC` | 0.0766 | n | -0.4118 | 1.439 | n | n |
| `W_FIN_EQUAL` | `WITHIN` | 0.0301 | n | -0.0167 | 0.4285 | Y | n |
| `W_FIN_TOP2_EQUAL` | `WITHIN` | 0.5399 | Y | -1.2831 | 8.6209 | n | n |
| `R_L1_05` | `REBAL` | 0.2771 | Y | 0.0361 | -0.2775 | Y | Y |
| `R_L1_10` | `REBAL` | 0.3276 | Y | -0.352 | 0.5702 | n | n |

### Read

≥1 residual challenger clears fill + NAV.

Repro: `PYTHONPATH=scripts python3 scripts/fin_residual_research_stagea.py`

Label: `FIN_RESIDUAL_RESEARCH_STAGEA_SCREEN_20260926__SIGNAL_HIT`
