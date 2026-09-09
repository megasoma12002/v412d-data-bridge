# Private financial holdings (民營金控) — Stage A re-screen

Generated: `2026-09-09T14:25:46.598226+00:00`
Status: **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** · Soft-Frozen **[0.6, 0.9]** · baseline **`LIVE_PUB_KD`** · live wire **false**
Capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`

## Absolute

| book | full CAGR | full MDD | heldout CAGR | heldout MDD |
|---|---:|---:|---:|---:|
| `LIVE_PUB_KD` | 13.26% | -21.72% | 16.96% | -21.72% |
| `LIVE_PUB_EQ` | 13.29% | -22.39% | 17.19% | -22.39% |
| `PRIV_EQ` | 16.39% | -27.47% | 20.74% | -27.47% |
| `PRIV_KD` | 16.48% | -26.81% | 20.91% | -26.81% |
| `ALL12_EQ` | 12.54% | -22.24% | 14.37% | -22.24% |
| `ALL12_KD` | 12.53% | -22.97% | 14.49% | -22.97% |

## vs LIVE_PUB_KD (current live intent)

| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | coexist |
|---|---:|---:|---:|---|---|---|---|
| `LIVE_PUB_EQ` | -0.783 | -0.666 | -0.232 | PASS | PASS | True | False |
| `ALL12_EQ` | -1.811 | -0.519 | 2.583 | PAUSE_REVIEW | PAUSE_REVIEW | False | False |
| `ALL12_KD` | -2.481 | -1.249 | 2.464 | PAUSE_REVIEW | PAUSE_REVIEW | False | False |
| `PRIV_KD` | -7.066 | -5.088 | -3.956 | PASS | PASS | True | False |
| `PRIV_EQ` | -7.637 | -5.746 | -3.783 | PASS | PASS | True | False |

## Reading

- Coexist (tip-clean + held-out>0): `none`
- Soft-Frozen membership stays 公股 R1; this only rewires Financial sleeve dollars on paper.
- Data fill applied: private E22 dividends + `adj_close` panel (`PRIVATE_FIN_DIV_ADJ_FILL.md`).
- PRIV books show **higher** held-out CAGR but **worse** MDD → score still strongly negative.
- No live universe expansion from this screen.
- Decision: **STOP** — `PRIVATE_FIN_HOLDINGS_DECISION_PACK.md`

Repro: `repro/private-fin-holdings-20260909/`
