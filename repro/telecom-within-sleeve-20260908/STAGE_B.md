# Telecom Within-Sleeve Allocation — Stage B

Generated: `2026-09-08T01:14:24.287099+00:00`
Ballot: **ACCEPT telecom within-sleeve charter** · Soft-Frozen **KEEP**
Execution: capital **3,000,000** · lot **1000** · `E22_v2s_tw`
Status: **STOP_NO_POSITIVE_HELDOUT_SCORE**
Live wire: **false** (e21 equal-split untouched)

## BASE (`TEL_EQUAL`)

- held-out MDD `-0.22385818655120981` · CAGR `0.17777827046900496`
- tip TEL weight `0.09758196133258296` · names w/ 張 `2` · cash w `0.015259679517615013`
- tip positions `{'2412': 11000.0, '3045': 1000.0, '4904': 0.0}`
- pct days TEL zero-board `0.03997613365155131` · near-3M band `{'n_days': 952, 'pct_days_tel_zero_board': 0.1407563025210084, 'mean_pre_telecom': 0.12399619297941622, 'mean_cash_weight': 0.02696749276394622}`

## Challengers vs BASE (held-out score; sealed report-only for top ≤2)

| id | heldout score | MDD↑pp | CAGRΔpp | tip TEL w | tip #names | pct TEL=0 | near3M TEL=0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `TEL_MIN_LOT_PACK` | -0.615 | -0.605 | 0.020 | 0.0728 | 1 | 0.001 | 0.005 |
| `TEL_TOP2_EQUAL` | -1.109 | -0.817 | 0.583 | 0.0712 | 1 | 0.170 | 0.360 |
| `TEL_TOP1` | -3.315 | -1.145 | 4.339 | 0.0725 | 1 | 0.121 | 0.196 |

## Top ≤2 sealed report-only

| id | sealed MDD↑pp | fragile (>2pp worse)? | tip positions |
|---|---:|---|---|
| `TEL_MIN_LOT_PACK` | 1.035 | False | `{'2412': 0.0, '3045': 0.0, '4904': 12000.0}` |
| `TEL_TOP2_EQUAL` | 1.247 | False | `{'2412': 0.0, '3045': 0.0, '4904': 11000.0}` |

## Hard rules

- Soft-Frozen sleeve clip module untouched
- Sealed not used for selection
- Passing ≠ live within-sleeve cutover (needs later ballot)

Repro: `repro/telecom-within-sleeve-20260908/`
