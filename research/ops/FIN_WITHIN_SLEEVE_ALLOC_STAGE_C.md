# Financial Within-Sleeve Allocation — Stage C

Generated: `2026-09-08T09:32:45.150841+00:00`
Human: **各檔各做各的**（除權息日不同 · 個股強弱時間不同）
Ballot: **金融也研究分開** · Soft-Frozen **KEEP** · live wire **false**
Execution: capital **500,000,000** · lot **1000** · Telecom=`TEL_EQUAL`
Status: **STAGE_C_CANDIDATES_LOCKED**

Stage B (hard TOP1/TOP2/MIN_LOT) already **STOP**. Stage C = softer per-name timing.

## Policies

| id | Rule |
|---|---|
| `FIN_EQUAL` | Equal split 4 names (BASE) |
| `FIN_RS_SOFT_TILT` | Buy $ soft-tilt by causal mom score; sells equal |
| `FIN_EXDIV_SKIP_BUY` | Skip buy on cash/stock ex-date for that name only |
| `FIN_RS_SOFT_TILT_EXDIV` | Soft-tilt buys among non-exdiv names |

Ex-div skip-buy day counts: `{'2880': 15, '2886': 17, '2892': 14, '5880': 16}`

## BASE (`FIN_EQUAL`)

- held-out MDD `-0.22577077146946323` · CAGR `0.18354255225903504`
- tip FIN w `0.8252276387273614` · names w/ 張 `4` · cash w `0.0071610379574543`

## Challengers vs BASE

| id | heldout score | MDD↑pp | CAGRΔpp | tip FIN w | tip #names | tip cash w |
|---|---:|---:|---:|---:|---:|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | 0.540 | 1.112 | 1.144 | 0.8333 | 4 | 0.0119 |
| `FIN_RS_SOFT_TILT` | 0.518 | 1.107 | 1.176 | 0.8327 | 4 | 0.0122 |
| `FIN_EXDIV_SKIP_BUY` | 0.334 | 0.572 | 0.476 | 0.8329 | 4 | 0.0121 |

## Top ≤2 sealed report-only

| id | sealed MDD↑pp | fragile? | tip positions |
|---|---:|---|---|
| `FIN_RS_SOFT_TILT_EXDIV` | 2.722 | False | `{'2880': 34099487.0, '2886': 9898427.0, '2892': 4035692.0, '5880': 348702.0}` |
| `FIN_RS_SOFT_TILT` | 2.777 | False | `{'2880': 34350348.0, '2886': 10259509.0, '2892': 3104939.0, '5880': 2435.0}` |

## Hard rules

- Soft-Frozen sleeve clip module untouched
- Live e21 FIN equal-split untouched
- Sealed not used for selection
- Stage B STOP stands; Stage C does not reopen hard concentration

Repro: `repro/fin-within-sleeve-stagec-20260908/`
