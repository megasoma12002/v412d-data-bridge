# Financial Within-Sleeve Allocation — Stage B

Generated: `2026-09-08T02:20:49.579468+00:00`
Ballot: **金融也研究分開** · Soft-Frozen **KEEP** · live wire **false**
Execution: capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`
Status: **STOP_NO_POSITIVE_HELDOUT_SCORE**

## BASE (`FIN_EQUAL`)

- held-out MDD `-0.22577077146946323` · CAGR `0.18354255225903504`
- tip FIN w `0.8252276387273614` · names w/ 張 `4` · cash w `0.0071610379574543`
- tip positions `{'2880': 46888250.0, '2886': 4752096.0, '2892': 28243.0, '5880': 3853.0}`

## Challengers vs BASE

| id | heldout score | MDD↑pp | CAGRΔpp | tip FIN w | tip #names | tip cash w |
|---|---:|---:|---:|---:|---:|---:|
| `FIN_MIN_LOT_PACK` | -0.112 | 0.069 | -0.362 | 0.8322 | 4 | 0.0120 |
| `FIN_TOP2_EQUAL` | -3.394 | 1.289 | 9.365 | 0.8440 | 2 | 0.0073 |
| `FIN_TOP1` | -11.313 | -3.824 | 14.977 | 0.8422 | 1 | 0.0083 |

## Top ≤2 sealed report-only

| id | sealed MDD↑pp | fragile? | tip positions |
|---|---:|---|---|
| `FIN_MIN_LOT_PACK` | 1.905 | False | `{'2880': 29300762.0, '2886': 8000.0, '2892': 7381.0, '5880': 46356810.0}` |
| `FIN_TOP2_EQUAL` | -1.509 | False | `{'2880': 10031421.0, '2886': 444.0, '2892': 5168348.0, '5880': 928.0}` |

## Hard rules

- Soft-Frozen sleeve clip module untouched
- Live e21 FIN equal-split untouched
- Sealed not used for selection

Repro: `repro/fin-within-sleeve-20260908/`
