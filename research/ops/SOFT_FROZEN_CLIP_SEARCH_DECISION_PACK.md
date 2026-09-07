# Soft-Frozen Clip Search — Decision Pack (Charter)

Date: 2026-09-07  
Status: **ACTIVE — awaiting human charter ballot**  
Soft-Frozen live: **KEEP** (FIN [0.50, 0.95] · TEL [0.03, 0.35] · 0050 [0.00, 0.35])  
Related: `SOFT_FROZEN_CLIP_SEARCH_CHARTER.md` · withdrawn floor-10: `SOFT_FROZEN_TEL_ETF_FLOOR_10_WITHDRAWN_2026-09-07.md`  
Charter execution context: **5M + 整張 1000** (live `DEFAULT_CAPITAL` stays 15M).

## What you are voting on

**Only** whether to open a **research-only** clip-box search under the charter.

You are **not** voting to change live Soft-Frozen clips.

## Ballots

| Ballot | Say | Effect |
|---|---|---|
| **ACCEPT charter** | `ACCEPT clip-search charter` | Allows Stage B grid harness PRs (paper only; Soft-Frozen untouched) |
| **DEFER** | `DEFER clip-search charter` | No implementation; revisit later |
| **REJECT** | `REJECT clip-search charter` | Close the line; Soft-Frozen KEEP |

## Non-ballots (do not conflate)

| Topic | Status |
|---|---|
| Soft-Frozen TEL/0050 floor → 10% | **WITHDRAWN** (#119 closed) |
| Soft-Frozen FIN band flip | Register #1 KEEP — needs separate Class D PR |
| E45 stitch | FORBIDDEN until second ACCEPT |
| “AI 完美比例” live-wire | **Out of scope** permanently under this pack |

## After ACCEPT charter

1. Implement `e16_clip_search_challenger` / repro grid (Stage B).  
2. Lock ≤3 candidates on held-out score; sealed report-only (Stage D).  
3. Optional observe sleeve (Stage E).  
4. **Only then** a new human ballot may consider Class D Soft-Frozen flip citing locked evidence.
