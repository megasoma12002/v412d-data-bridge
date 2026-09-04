# Research Reopen Authorization — All Tracks

Date: **2026-09-04**  
Authority: explicit user directive — **「准許每條進行研究」**  
Status: **`RESEARCH_REOPENED`** (challenger mode only)

## What was authorized

Research may proceed on **every** previously closed / deferred track below.  
This is **not** permission to edit SOFT_FROZEN files in place, relax HARD_FROZEN, or auto-promote.

| Track | Prior state | New state | Official baseline preserved |
|---|---|---|---|
| E22 dividend path | E22_v2 SOFT_FROZEN | **E22_v3+ challengers allowed** | `forward/e22_v2/`, `e21` |
| E16 / E18 | SOFT_FROZEN | **Challengers allowed** | `forward/e21/`, E16/E18 specs |
| E45 | Decision B (not promoted) | **Promotion re-review + challengers** | V4.12-D formal |
| Alpha 3A | CLOSED_DEFERRED | **REOPENED** (new-info only) | 3B still forbids same-panel grids |
| G4 hedge | CLOSED_NOT_REQUIRED | **REOPENED for research** | No silent add into E16 |

## Absolute constraints (unchanged)

1. **HARD_FROZEN** (PIT, Exact T+1, no lookahead, no history rewrite) — never relaxed.  
2. Every change → **separate challenger folder** + side-by-side vs preserved baseline.  
3. Promotion only after **PASS evidence + explicit approval phrase** (as with E22_v2).  
4. Same-panel TECH2 / S9A1 / 2.5%·0.70 gate forcing remains **forbidden** (3B).

## Track charters

- `research/reopen/E22_V3_CHARTER.md`
- `research/reopen/E16_E18_CHALLENGER_CHARTER.md`
- `research/reopen/E45_PROMOTION_REREVIEW_CHARTER.md`
- `research/reopen/ALPHA_3A_CHARTER.md`
- `research/reopen/G4_HEDGE_REOPEN_CHARTER.md`
- Round-1 runner: `scripts/research_reopen_round1.py`

## Approval phrase (this reopen)

`AUTHORIZE_RESEARCH_ALL_TRACKS_CHALLENGER_ONLY — E22_v3, E16/E18, E45 re-review, Alpha 3A, G4 hedge; HARD_FROZEN intact; no in-place SOFT_FROZEN edits.`
