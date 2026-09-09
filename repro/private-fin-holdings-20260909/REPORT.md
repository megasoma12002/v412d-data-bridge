# Private financial holdings (民營金控) — Stage A re-screen

Generated: `2026-09-09T14:09:29.967585+00:00`
Status: **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** · Soft-Frozen **[0.6, 0.9]** · baseline **`LIVE_PUB_KD`** · live wire **false**
Capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`

## Absolute

| book | full CAGR | full MDD | heldout CAGR | heldout MDD |
|---|---:|---:|---:|---:|
| `LIVE_PUB_KD` | 13.26% | -21.72% | 16.96% | -21.72% |
| `LIVE_PUB_EQ` | 13.29% | -22.39% | 17.19% | -22.39% |
| `PRIV_EQ` | 10.19% | -28.49% | 15.00% | -27.78% |
| `PRIV_KD` | 10.55% | -28.49% | 15.70% | -26.95% |
| `ALL12_EQ` | 11.28% | -22.28% | 14.14% | -22.28% |
| `ALL12_KD` | 11.41% | -22.09% | 14.32% | -22.09% |

## vs LIVE_PUB_KD (current live intent)

| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | coexist |
|---|---:|---:|---:|---|---|---|---|
| `LIVE_PUB_EQ` | -0.783 | -0.666 | -0.232 | PASS | PASS | True | False |
| `ALL12_KD` | -1.686 | -0.370 | 2.632 | PAUSE_REVIEW | PAUSE_REVIEW | False | False |
| `ALL12_EQ` | -1.967 | -0.561 | 2.812 | PAUSE_REVIEW | PAUSE_REVIEW | False | False |
| `PRIV_KD` | -5.855 | -5.227 | 1.256 | PASS | PASS | True | False |
| `PRIV_EQ` | -7.036 | -6.058 | 1.956 | PASS | PASS | True | False |

## Reading

- Coexist (tip-clean + held-out>0): `none`
- Soft-Frozen membership stays 公股 R1; this only rewires Financial sleeve dollars on paper.
- Private dividend E22 coverage incomplete — treat PRIV/ALL12 levels as directional.
- No live universe expansion from this screen.
- Decision: **STOP** — `PRIVATE_FIN_HOLDINGS_DECISION_PACK.md`

Repro: `repro/private-fin-holdings-20260909/`
