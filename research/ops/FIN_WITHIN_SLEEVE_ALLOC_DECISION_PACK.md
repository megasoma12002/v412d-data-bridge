# Financial Within-Sleeve Allocation — Decision Pack

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** · Stage B **STOP** · Stage C **`STAGE_C_CANDIDATES_LOCKED`**  
Soft-Frozen: **KEEP** · capital **500M** (research exec) · board-lot **1000**  
Charter: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md`  
Stage B: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_B.md`  
Stage C: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.md` · live wire **false**

## Ballot

| Ballot | Say | Effect | Result |
|---|---|---|---|
| **ACCEPT charter** | `金融也研究分開` / `ACCEPT fin within-sleeve charter` | Stage B paper OK | **ACCEPTED 2026-09-08** |
| **DEFER / REJECT** | — | No code | — |

## Stage results (paper)

| Stage | Best held-out score vs `FIN_EQUAL` | Verdict |
|---|---|---|
| B hard (TOP1/TOP2/MIN_LOT) | −0.112 (`FIN_MIN_LOT_PACK`) | **STOP** |
| C soft (RS / ex-div) | **+0.540** (`FIN_RS_SOFT_TILT_EXDIV`) | **CANDIDATES_LOCKED** |

Stage C top ≤2 (selection held-out; sealed report-only):

1. `FIN_RS_SOFT_TILT_EXDIV` — held-out score +0.540 · sealed MDD↑ +2.72pp (not fragile)
2. `FIN_RS_SOFT_TILT` — held-out score +0.518 · sealed MDD↑ +2.78pp (not fragile)

`FIN_EXDIV_SKIP_BUY` alone also positive (+0.334) but ranks 3rd.

Human rationale confirmed empirically: **各檔各做各的** (ex-div skip + soft RS) beats equal-split on the predeclared score; hard concentration (Stage B) did not.

## Still required later

| Ballot | Effect |
|---|---|
| **ACCEPT Stage C dual-paper observe** | Observe top policy beside `FIN_EQUAL` (no live) |
| **ACCEPT live FIN within-sleeve cutover** | Wire chosen policy into `e21` |

## Non-ballots

| Topic | Status |
|---|---|
| Soft-Frozen clips | **KEEP** |
| Live FIN wire | **NOT** this ballot — Stage C lock ≠ cutover |
| Stage B hard policies | Remain **STOP** (do not reopen) |
