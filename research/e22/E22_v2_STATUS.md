# E22_v2 Status — Current Official Dividend Path

Date approved: **2026-09-04**  
Version ID: **`E22_v2_CASH_EX_OFFICIAL_PATH`**  
Governance class: **`SOFT_FROZEN`**

## Approval

Phrase received:

> APPROVE E22_v2_CASH_EX_OFFICIAL_PATH — wire cash_ex_date credits into official exec path as new SOFT_FROZEN version; preserve forward/e21 forever.

| Role | Decision | Date |
|---|---|---|
| Governance / human | **APPROVED** | 2026-09-04 |
| Research package | `research/e22/E22_PROMOTION_PACKAGE.md` | 2026-09-04 |

## Official surfaces

| Role | Path |
|---|---|
| Official script | `scripts/e22_v2_forward_pipeline.py` |
| Official QC | `scripts/e22_v2_qc.py` |
| Official ledgers | `forward/e22_v2/` |
| Dividend events | `data/dividend_events/e22_dividend_events.csv` |
| Shared market feed (read-only) | `forward/e21/live_market.csv` |

## Mechanism

1. E16 targets (same as E21)  
2. Exact T+1 open fills (E18)  
3. **NEW vs E21 loop:** credit `shares × cash_dividend` on `cash_ex_date` into cash  

## Cutover

- Seeded from `forward/e21/` portfolio + **pending** orders only  
- Seed date: `2026-09-03`  
- **No** dividend backfill into prior E21 history  
- `forward/e21/` remains readable forever as the pre-v2 live baseline  

## Preserved prior versions

| Artifact | Role |
|---|---|
| `forward/e21/` | Prior live E16+E18 path (no dividend cash in fill loop) |
| `scripts/e21_forward_pipeline.py` | Prior official runner (unchanged) |
| `forward/e22_challenger/` | Paper challenger that justified promotion |
| E22 event ledger / hold-vs-sell research | Prior SOFT_FROZEN research surface |

## Daily ops

```bash
python scripts/e22_v2_forward_pipeline.py
python scripts/e22_v2_qc.py
```

## Challenger rule

Further changes to dividend timing / tax treatment require a **new** challenger folder and promotion path — do not edit `e22_v2` in place and still call it v2.
