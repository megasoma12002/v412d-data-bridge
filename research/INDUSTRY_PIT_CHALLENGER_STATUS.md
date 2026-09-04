# Industry PIT Challenger — 2026-09-04

Pack: `data/research_advanced/industry_pit_challenger/`  
Script: `scripts/fetch_industry_pit_challenger.py`  
Contract: **CHALLENGER_SPARSE_NOT_TWT58U** — does **not** patch E50-A0.

## What we built (free)

| Artifact | Rows | Notes |
|---|---:|---|
| `industry_reclass_events.csv` | 76 | TWSE 62 + TPEx 13 + 1 taxonomy rename; **0** missing `old_industry` |
| `snapshot_isin_class_main_listed.csv` | 1,054 | Live ISIN named industries (listed equities) |
| `snapshot_twse_current.csv` | 1,094 | OpenAPI industry **codes** + ISIN names |
| `industry_code_map.csv` | 32 | 2-digit code → name |
| `wayback_isin_snapshots/` | 2 dates | 2018-07-19, 2023-12-25 (`C_public` **partial** ~320 names) |
| `event_touched_sparse_pit.csv` | 209 | As-of reconstruction **only for event-touched tickers** |

### Event coverage (public announcements / media reprints)

| Effective | Market | Count | Source class |
|---|---|---:|---|
| 2021-06-01 | TWSE | 11 | Chinatimes reprint of TWSE annual adjust |
| 2022-06-01 | TWSE | 3 | Chinatimes |
| 2023-07-03 | TWSE | 47 + taxonomy rename | TWSE ann. 臺證上一字第1121802250 + 月訊#76 + Yahoo reprint (old industries for 5 residual names) |
| 2026-06-01 | TWSE | 1 (`2601` 益航) | CNA |
| 2026-06-01 | TPEx | 13 | MoneyDJ / CNA |

### QC

- Event `new_industry` vs live ISIN (normalized): **1 residual** — `3054` event→食品工業 vs current→電子通路業 (possible later move; left flagged, not force-edited).
- A0 / frozen ledgers: **untouched**.

## Still not true historical industry PIT

| Need | Status |
|---|---|
| Daily full-universe map | **TWT58U** E-Shop (from 2019-12-23) — still paid |
| Pre-2019 / longer PIT | **TEJ** company-attribute PIT (~2013+) — paid |
| Dense free archive | Wayback `class_main` pre-2023 **not available**; `C_public` archives are **partial** |

## How to use (research only)

1. Industry-neutral **event study** on the ~75 reclass names around `effective_date`.
2. Do **not** backfill non-event tickers from current industry.
3. Do **not** promote industry-neutral alpha until TWT58U/TEJ lands.

## Reproduce

```bash
python3 scripts/fetch_industry_pit_challenger.py
```
