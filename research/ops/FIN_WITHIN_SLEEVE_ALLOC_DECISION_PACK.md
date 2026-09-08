# Financial Within-Sleeve Allocation — Decision Pack

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** · Stage B **STOP** · Stage C **LOCKED** · Stage D **OPERATING OBSERVE** · Mix probe **COEXIST_CANDIDATE_FOUND**  
Soft-Frozen: **KEEP** · capital **500M** (research exec) · board-lot **1000**  
Charter: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md`  
Stage B: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_B.md`  
Stage C: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.md`  
Dual-paper: `FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPEN.md` · live wire **false**  
Mix: `FIN_EQUAL_RS_EXDIV_MIX.md`

## Ballot

| Ballot | Say | Effect | Result |
|---|---|---|---|
| **ACCEPT charter** | `金融也研究分開` | Stage B paper OK | **ACCEPTED 2026-09-08** |
| **OPEN dual-paper observe** | `dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL` | Stage D observe | **OPEN / OPERATING 2026-09-08** |

## Stage results (paper)

| Stage | Best held-out score vs `FIN_EQUAL` | Verdict |
|---|---|---|
| B hard (TOP1/TOP2/MIN_LOT) | −0.112 (`FIN_MIN_LOT_PACK`) | **STOP** |
| C soft (RS / ex-div) | **+0.540** (`FIN_RS_SOFT_TILT_EXDIV`) | **CANDIDATES_LOCKED** |
| D dual-paper | `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` @ 500M | **OPERATING OBSERVE** |
| Mix λ-grid | **`MIX_L75`** held **+0.129** · tip YTD/1y **PASS** | **COEXIST_CANDIDATE_FOUND** |

## Still required later

| Ballot | Effect |
|---|---|
| **ACCEPT live FIN within-sleeve cutover** | Wire chosen policy into `e21` |
| Optional: open `MIX_L75` observe leg | Third paper ledger or replace RS_EXDIV challenger |

## Non-ballots

| Topic | Status |
|---|---|
| Soft-Frozen clips | **KEEP** |
| Live FIN wire | **NOT** this ballot — observe ≠ cutover |
| Stage B hard policies | Remain **STOP** |
| Mix live wire | **FORBIDDEN** until dedicated ACCEPT |
