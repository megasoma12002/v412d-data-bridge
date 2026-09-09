# Telecom Within-Sleeve Async — Stage D (FIN-parallel)

Generated: `2026-09-09T13:38:38.195989+00:00`
Human: **電信三檔也做跟金融股一樣拆開的研究**
Status: **STOP_NO_POSITIVE_HELDOUT_SCORE** · Soft-Frozen **[0.6, 0.9]** · FIN=`KD_OPT` · live wire **false**
Capital **500,000,000** · lot **1000** · BASE=`TEL_EQUAL`

Ex-div skip-buy day counts: `{'2412': 15, '3045': 15, '4904': 15}`

## vs TEL_EQUAL (held-out)

| id | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | tip #TEL |
|---|---:|---:|---:|---|---|---|---:|
| `TEL_MIX_EQUAL_RS_EXDIV` | -0.045 | 0.066 | 0.222 | PASS | PASS | True | 2 |
| `TEL_EXDIV_SKIP_BUY` | -0.415 | -0.202 | 0.425 | PASS | PASS | True | 2 |
| `TEL_RS_SOFT_TILT_EXDIV` | -0.486 | -0.258 | 0.456 | PASS | PASS | True | 2 |
| `TEL_RS_SOFT_TILT` | -0.501 | -0.282 | 0.438 | PASS | PASS | True | 2 |

## Reading

- Tip-clean + held-out>0: `none`
- Prior pack Stage C (`TEL_DIVERSIFY_PACK`) remains separate evidence @ 500M.
- No live Telecom cutover from this screen.

Repro: `repro/telecom-within-sleeve-async-20260909/`
