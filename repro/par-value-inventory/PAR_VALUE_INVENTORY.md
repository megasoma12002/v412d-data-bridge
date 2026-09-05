# PAR_VALUE_INVENTORY

- generated: `2026-09-05T14:21:22.225995+00:00`
- coverage_pass_for_promote: **True**
- verified / lookup / etf / expand: **8** / **0** / **1** / **1**
- method: `TWSE openapi t187ap03_L field 普通股每股面額 (+ watchlist)`
- extensible: watchlist `data/corporate_actions/par_value_watchlist.csv` + `--add-codes` + `--fetch-twse`

| Code | Role | Provisional | Verified | Status | Source | As-of |
|---|---|---:|---:|---|---|---|
| 2880 | soft_frozen_fin | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 2886 | soft_frozen_fin | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 2892 | soft_frozen_fin | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 5880 | soft_frozen_fin | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 2412 | telecom | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 3045 | telecom | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 4904 | telecom | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 2330 | expand | 10.0 | 10.0 | VERIFIED | TWSE_openapi_t187ap03_L | 2026-09-04 |
| 0050 | etf | nan | None | ETF_RULES_LOOKUP_NEEDED | — | — |

Charter: `research/ops/PAR_VALUE_LOOKUP_CHARTER.md`

Item 1 (odd-lot): Soft-Frozen FIN + telecom equity pars are the promote gate.
Future codes: add to watchlist or `--add-codes` — does not auto-flip DEFAULT.

Soft-Frozen KEEP. No DEFAULT_BOOKS_VERSION flip from this script.
