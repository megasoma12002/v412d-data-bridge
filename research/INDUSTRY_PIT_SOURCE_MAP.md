# Industry PIT — Source Map (T3)

Date: **2026-09-04**  
Companion: `research/INDUSTRY_PIT_CHALLENGER_STATUS.md`, `data/research_advanced/industry_pit_challenger/`

## Free / done this session

| Source | PIT? | Result |
|---|---|---|
| TWSE / TPEx **reclass announcements** (+ media reprints) | Event-level | `industry_reclass_events.csv` (76 rows) |
| ISIN `class_main` listed equities | Current only | `snapshot_isin_class_main_listed.csv` |
| TWSE OpenAPI `t187ap03_L` | Current codes | Joined to names → `snapshot_twse_current.csv` + `industry_code_map.csv` |
| Wayback ISIN `C_public.jsp` | Sparse / **partial** | 2018-07-19, 2023-12-25 (~320 names each) |

## Still required for full PIT

| Source | Access | Coverage | Notes |
|---|---|---|---|
| TWSE E-Shop **TWT58U** | Paid ~NT$500/mo | Daily from **2019-12-23** | Official code→industry; archive then build `industry_pit.csv` under `repro/` |
| **TEJ** company attribute / `TWN/AIND` | Paid | PIT from ~**2013** | Vendor taxonomy; QC vs TWSE codes before alpha use |
| Bloomberg / Refinitiv GICS | Paid | Long history | Different taxonomy — not a drop-in for TWSE industry |

## Not substitutes

| Source | Why not |
|---|---|
| FinMind `TaiwanStockInfo` | Current snapshot |
| TWMD `issuer-classification` | Docs: current-state stamp, not a history series |
| OpenFun listed refs | Bot-wall / current only |
| Wayback alone | Too sparse; `C_public` incomplete; no pre-2023 `class_main` hits here |

## Next actionable path

1. Keep using the **event challenger** for reclass event studies only.
2. If industry-neutral alpha reopens: **buy TWT58U archive** (and optionally TEJ for pre-2019).
3. Never silent-patch E50-A0 with current industry.
