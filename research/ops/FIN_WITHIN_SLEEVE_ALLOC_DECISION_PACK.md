# Financial Within-Sleeve Allocation — Decision Pack

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** · Stage B **STOP** · Stage C **LOCKED** · Stage D **OPERATING OBSERVE** (+**MIX_L75**) · Mix probe **COEXIST_CANDIDATE_FOUND** · Posture **LOCKED**  
Soft-Frozen: **KEEP** · capital **500M** (research exec) · board-lot **1000**  
Charter: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md`  
Stage B: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_B.md`  
Stage C: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.md`  
Dual-paper: `FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPEN.md` · live wire **false**  
Mix: `FIN_EQUAL_RS_EXDIV_MIX.md`  
Posture: `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md`  
Portfolio: `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` (**KEEP** FIN triad · archive other research lines)  
Pre-exdiv KD probe: `FIN_PRE_EXDIV_KD_PROBE.md` (**PAPER_PROBE** · Yahoo K9/D9)  
KD NAV / optimize: `FIN_PRE_EXDIV_KD_NAV.md` · `FIN_PRE_EXDIV_KD_OPTIMIZE.md` (**optimal `KD_APR15_MAY15_Klt30_T15`**)  
Objective scan: `FIN_OBJECTIVE_REGULARITY.md`

## Ballot

| Ballot | Say | Effect | Result |
|---|---|---|---|
| **ACCEPT charter** | `金融也研究分開` | Stage B paper OK | **ACCEPTED 2026-09-08** |
| **OPEN dual-paper observe** | `dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL` | Stage D observe | **OPEN / OPERATING 2026-09-08** |
| **ADD MIX_L75 observe** | `把 MIX_L75 加進 dual-paper observe` | Third paper ledger | **OPERATING 2026-09-08** |
| **LOCK observe posture** | 維持 OPERATING · 不開 live · 窗後再選 · 先不做 TOP1/stitch | Stage D posture | **LOCKED 2026-09-08** |
| **LOCK research portfolio** | FIN 三本（重心 MIX_L75）+ E45 A05/C35 + 月結閘門；其餘封存 | Active agenda | **LOCKED 2026-09-08** |
| **OPEN pre-exdiv KD probe** | Yahoo K9/D9 · May–Jun K&lt;25 · pre-ex T−10…T−1 | Paper probe only | **OPEN 2026-09-09** |

## Accepted operating posture (2026-09-08)

1. **Maintain OPERATING** — month-end refresh via `ops_month_end_paper_pack.py` for `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75`; compare tip (RS may PAUSE; MIX_L75 should stay cleaner) and held-out.
2. **No live wire** — Soft-Frozen **KEEP**; cutover requires a dedicated **ACCEPT** ballot.
3. **Choose after observe window** — if tip stays clean and held-out holds → prefer **`MIX_L75`**; if max MDD lift is required and tip PAUSE is tolerable → consider pure **RS_EXDIV**.
4. **Do not** — reopen Stage B hard TOP1/TOP2; stitch / live `e21` wire on this line.

## Stage results (paper)

| Stage | Best held-out score vs `FIN_EQUAL` | Verdict |
|---|---|---|
| B hard (TOP1/TOP2/MIN_LOT) | −0.112 (`FIN_MIN_LOT_PACK`) | **STOP** |
| C soft (RS / ex-div) | **+0.540** (`FIN_RS_SOFT_TILT_EXDIV`) | **CANDIDATES_LOCKED** |
| D dual-paper | `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ **`MIX_L75`** @ 500M | **OPERATING OBSERVE** |
| Mix λ-grid | **`MIX_L75`** held **+0.129** · tip YTD/1y **PASS** | **COEXIST_CANDIDATE_FOUND** |

## Still required later

| Ballot | Effect |
|---|---|
| **ACCEPT live FIN within-sleeve cutover** | Wire chosen policy (`MIX_L75` or RS) into `e21` |

## Non-ballots

| Topic | Status |
|---|---|
| Soft-Frozen clips | **KEEP** |
| Live FIN wire | **NOT** this ballot — observe ≠ cutover |
| Stage B hard policies | Remain **STOP** |
| Mix / RS live wire | **FORBIDDEN** until dedicated ACCEPT |
| E45 stitch on this line | **FORBIDDEN** |
