# E45 Sleeve-Local Observe — OPEN Ballot **DRAFT**

Date: 2026-09-06  
Status: **SUPERSEDED — ACCEPTED 2026-09-06** → see `E45_SLEEVE_LOCAL_OBSERVE_OPEN.md`  
Human ballot (proposed name): **`E45 OPEN sleeve-local observe`**  
Authority (if accepted): Register #6c follow-on · `E45_SLEEVE_LOCAL.md` · `E45_SLEEVE_LOCAL_DEEP_DIVE.md` · `E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md` · `E45_STAGE12_STATUS.md`  
Chinese translation (non-binding mirror): `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN_BALLOT_DRAFT.zh-TW.md`

> **Not authorized.** This file is a **draft ballot only**.  
> It does **not** OPEN an observe sleeve, does **not** wire month-end, does **not** flip Soft-Frozen / DEFAULT, and does **not** authorize stitch.  
> Until a human marks **ACCEPT** on this ballot (separate explicit action), sleeve-local remains **PAPER ONLY**.

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
−13.16% claim: **`RETIRED_HISTORICAL_NARRATIVE`**  
Parent observe sleeves still OPERATING (unchanged by this draft): FULL E45 + blend-α=0.25 + blend-α=0.05

---

## Proposed ballot (inactive until ACCEPT)

| Field | Proposed value |
|---|---|
| Choice | **OPEN sleeve-local observe** (paper parallel only) |
| Primary challenger (deep-dive preferred) | **`SLEEVE_FIN_ONLY_A10`** — E45 `E3_VOLTARGET_WINNER` applied **only** to Financial sleeve @ **α=0.10** |
| Base book | `BASE_E16_E18_E22_v2s` |
| Overlay | whole-book exposure = 1 except Financial sleeve scaled by `exposure = 0.90·1 + 0.10·E3_VOLTARGET_WINNER` |
| Cadence (if ACCEPT) | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |
| Retire FULL / A25 / A05? | **No** — all remain OPERATING |

### Alternate (not default)

If ACCEPT prefers the milder P6 structure instead of deep-dive preferred:

| Alternate | Spec |
|---|---|
| `SLEEVE_FIN_0050_A05` | Financial + 0050 @ α=0.05 (leave Telecom) |

Default proposal remains **FIN_ONLY @ α=0.10** unless the ACCEPT note explicitly selects the alternate.

---

## Why this sleeve (paper evidence)

From `E45_SLEEVE_LOCAL_DEEP_DIVE.md` (post P1–P7):

1. Held-out preferred @1×: **`FIN_ONLY_A10`** (score **~0.285**) beats whole-book **`ALL_A05`** (~0.222).
2. Cost 2× twin still positive (score **~0.319**) — not a turnover bomb at this intensity.
3. Crisis-year MDD help still **~84% concentrated in 2020** — same honesty constraint as whole-book A05.
4. Structure edge (where α applies) is the reason to observe sleeve-local **separately** from whole-book A05; do not conflate the two sleeves.

Opening (only after ACCEPT) would be **observe-only**. Expect YTD/1y **PAUSE_REVIEW** at current tip — same as A05/A25. Observe ≠ stitch.

---

## Pre-open checklist (to be re-confirmed at ACCEPT)

| # | Item | Draft status |
|---|---|---|
| 1 | Soft-Frozen live clip remains [0.50, 0.95] | **YES** (current) |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** (current) |
| 3 | Parent sleeve-local paper + deep-dive present | **YES** |
| 4 | −13.16% still RETIRED | **YES** |
| 5 | No stitch / live-wire PR bundled | **REQUIRED at ACCEPT** |
| 6 | Month-end owner = `ops_month_end_paper_pack.py` / research/ops | **REQUIRED at ACCEPT** (scripts not built until ACCEPT) |
| 7 | PAUSE_REVIEW policy understood (observe ≠ stitch) | **REQUIRED** |
| 8 | FULL + A25 + A05 observe sleeves left operating in parallel | **YES** (must remain) |
| 9 | Explicit human ACCEPT string recorded | **MISSING — blocks OPEN** |

---

## Artifacts if ACCEPT (not created by this draft)

| Artifact | Planned path (post-ACCEPT only) |
|---|---|
| OPEN ballot (promoted) | `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.md` |
| Ledgers | `scripts/e45_sleeve_local_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e45_sleeve_local_month_end_monitor.py` |
| Repro | `repro/e45-sleeve-local-dual-paper-observe/` |
| Monitor JSON | `research/gaps/E45_SLEEVE_LOCAL_MONTH_END_MONITOR.json` |
| Pack wire | add steps to `ops_month_end_paper_pack.py` |

**This DRAFT does not create or wire any of the above.**

---

## Explicit non-actions (binding while DRAFT)

1. Do **not** treat this file as OPEN authority.  
2. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
3. Do **not** flip Soft-Frozen or DEFAULT books.  
4. Do **not** auto-build ledgers / month-end / pack steps from this draft alone.  
5. Do **not** retire FULL / A25 / A05 observe sleeves.  
6. Do **not** invent a −13.16% replacement number.  
7. Do **not** open crisis-gate or mild-`max_cut` observe from this ballot.

---

## ACCEPT / REJECT rubric (human)

**ACCEPT** requires an explicit note, e.g.:

> `E45 ACCEPT OPEN sleeve-local observe` — primary `SLEEVE_FIN_ONLY_A10` (or alternate `SLEEVE_FIN_0050_A05`) — Soft-Frozen KEEP — stitch FORBIDDEN

**REJECT / DEFER** examples:

> `E45 REJECT sleeve-local observe` — keep PAPER only  
> `E45 DEFER sleeve-local observe` — continue FULL+A25+A05 cadence only

Until one of the above is recorded, status stays **DRAFT / NOT OPEN**.

---

## Parent evidence

- `research/e45/E45_SLEEVE_LOCAL.md` (P6)  
- `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md` (post-P7 densify)  
- `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`  
- `research/ops/E45_OBSERVE_SLEEVES_STATUS.md` (sleeve-local row: NOT OPEN)

---

## Label

`E45_SLEEVE_LOCAL_OBSERVE_OPEN_BALLOT_DRAFT_2026-09-06__AWAITING_HUMAN_ACCEPT__NOT_OPEN__STITCH_FORBIDDEN`
