# 金融公 / 金融民 dual-sleeve — Stage A re-screen

Generated: `2026-09-09T14:40:17.742961+00:00`
Status: **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** · Soft-Frozen **[0.6, 0.9]** · baseline **`LIVE_PUB_KD`** · live wire **false**
Mechanism: Soft-Frozen Financial weight kept; dollars split 公股/民營 coexist.
Capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL` · 公 within=`KD_OPT`

## Absolute

| book | pub_share | priv | full CAGR | full MDD | heldout CAGR | heldout MDD |
|---|---:|---|---:|---:|---:|---:|
| `LIVE_PUB_KD` | 1.00 | `FIN_EQUAL` | 13.26% | -21.72% | 16.96% | -21.72% |
| `DUAL_P85_KD` | 0.85 | `FIN_PRE_EXDIV_KD` | 14.36% | -23.27% | 18.95% | -23.27% |
| `DUAL_P85_EQ` | 0.85 | `FIN_EQUAL` | 14.34% | -23.32% | 18.94% | -23.32% |
| `DUAL_P75_KD` | 0.75 | `FIN_PRE_EXDIV_KD` | 14.69% | -24.09% | 19.45% | -24.09% |
| `DUAL_P75_EQ` | 0.75 | `FIN_EQUAL` | 14.71% | -24.11% | 19.54% | -24.11% |
| `DUAL_P50_KD` | 0.50 | `FIN_PRE_EXDIV_KD` | 15.19% | -24.44% | 19.90% | -24.44% |
| `DUAL_P60_KD` | 0.60 | `FIN_PRE_EXDIV_KD` | 15.09% | -24.47% | 19.92% | -24.47% |
| `DUAL_P60_EQ` | 0.60 | `FIN_EQUAL` | 15.10% | -24.48% | 20.02% | -24.48% |
| `DUAL_P50_EQ` | 0.50 | `FIN_EQUAL` | 15.15% | -24.96% | 19.99% | -24.96% |

## vs LIVE_PUB_KD

| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | tip公/民 | coexist |
|---|---:|---:|---:|---|---|---|---|---|
| `DUAL_P85_KD` | -2.541 | -1.545 | -1.990 | PASS | PASS | True | 4/6 | False |
| `DUAL_P85_EQ` | -2.591 | -1.598 | -1.987 | PASS | PASS | True | 4/6 | False |
| `DUAL_P75_KD` | -3.614 | -2.368 | -2.493 | PASS | PASS | True | 4/6 | False |
| `DUAL_P75_EQ` | -3.681 | -2.391 | -2.580 | PASS | PASS | True | 3/6 | False |
| `DUAL_P50_KD` | -4.188 | -2.716 | -2.945 | PASS | PASS | True | 3/6 | False |
| `DUAL_P60_KD` | -4.230 | -2.745 | -2.969 | PASS | PASS | True | 3/6 | False |
| `DUAL_P60_EQ` | -4.286 | -2.755 | -3.062 | PASS | PASS | True | 4/6 | False |
| `DUAL_P50_EQ` | -4.757 | -3.242 | -3.031 | PASS | PASS | True | 4/6 | False |

## Reading

- Coexist (tip-clean + held-out>0): `none`
- Not the same as PRIV-replace Stage A — here 公股 stays in book.
- Soft-Frozen router features remain 公股; no live 4-sleeve Soft-Frozen rewrite this Stage.
- No live wire from this screen.

Repro: `repro/fin-pub-priv-dual-sleeve-20260909/`
