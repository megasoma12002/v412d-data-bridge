# Stage 8b add-on — 00981A / 00991A

Date: **2026-09-04**  
Artifacts: `repro/stage8b-00981a-00991a-20260904/`

| ETF | Listing window | Status |
|---|---|---|
| **00981A** | 2025-05-27 → 2026-09-04 (314 calendar rows) | Ran, but only **62** post-warmup NAV days |
| **00991A** | 2025-12-18 → 2026-09-04 (172 rows) | **TOO_SHORT** (needs ≥ warmup 252 + 60) |

## Headline numbers (00981A only — **not actionable**)

| Book | CAGR | MDD | Util | n days |
|---|---:|---:|---:|---:|
| BASE_w | 0.83 | −0.069 | 0.796 | 62 |
| SLEEVE4 | 0.73 | −0.028 | 0.712 | 62 |
| RISKOFF | 0.86 | −0.033 | 0.842 | 62 |

RISKOFF clears the numeric util/MDD bar vs BASE on this tiny window.

## Decision: `STAGE8B_00981A_00991A_INCONCLUSIVE_TOO_SHORT`

- **00991A**: cannot run under the frozen warmup contract.
- **00981A**: “interesting” print is **noise** — ~3 months of live trading after warmup; CAGR ~80%+ is not a research signal.
- **No promote.** Do not add either name to E22_v2.

Revisit only after each ETF has ≥ ~2–3 years of daily history (and preferably dividend-adjusted prices).
