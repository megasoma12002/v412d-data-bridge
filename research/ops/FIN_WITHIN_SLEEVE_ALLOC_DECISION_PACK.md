# Financial Within-Sleeve Allocation — Decision Pack

Date: 2026-09-08 · KD_OPT observe 2026-09-09  
Status: **CHARTER ACCEPTED** · Stage B **STOP** · Stage C **LOCKED** · Stage D **OPERATING OBSERVE** (+**MIX_L75** +**KD_OPT**) · Mix probe **COEXIST_CANDIDATE_FOUND** · KD **OPTIMAL_SELECTED_OBSERVE** · Posture **LOCKED**  
Soft-Frozen: **KEEP** · capital **500M** (research exec) · board-lot **1000**  
Charter: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md`  
Stage B: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_B.md`  
Stage C: `FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.md`  
Dual-paper: `FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPEN.md` · live **`KD_OPT` ACCEPTED**  
Mix: `FIN_EQUAL_RS_EXDIV_MIX.md`  
Posture: `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md`  
Cutover: `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` · checklist **ACCEPTED**  
Portfolio: `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` (**KEEP** FIN quartet · archive other research lines)  
Pre-exdiv KD probe: `FIN_PRE_EXDIV_KD_PROBE.md` (**PAPER_PROBE** · Yahoo K9/D9)  
KD NAV / optimize: `FIN_PRE_EXDIV_KD_NAV.md` · `FIN_PRE_EXDIV_KD_OPTIMIZE.md` (**optimal `KD_APR15_MAY15_Klt30_T15`** → observe **`KD_OPT`** → **live**)  
Post-exdiv autumn: `FIN_POST_EXDIV_AUTUMN_PROBE.md` · NAV · `FIN_POST_EXDIV_AUTUMN_OPTIMIZE.md` · dual `FIN_KD_AUTUMN_DUAL_SEASON.md` (**STOP** · no lift vs KD_OPT)  
Objective scan: `FIN_OBJECTIVE_REGULARITY.md`
EQUAL×KD mix probe: `FIN_EQUAL_KD_OPT_MIX.md` (**paper only** · coexist grid)

## Ballot

| Ballot | Say | Effect | Result |
|---|---|---|---|
| **ACCEPT charter** | `金融也研究分開` | Stage B paper OK | **ACCEPTED 2026-09-08** |
| **OPEN dual-paper observe** | `dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL` | Stage D observe | **OPEN / OPERATING 2026-09-08** |
| **ADD MIX_L75 observe** | `把 MIX_L75 加進 dual-paper observe` | Third paper ledger | **OPERATING 2026-09-08** |
| **LOCK observe posture** | 維持 OPERATING · 不開 live · 窗後再選 · 先不做 TOP1/stitch | Stage D posture | **LOCKED 2026-09-08** |
| **LOCK research portfolio** | FIN observe + E45 A05/C35 + 月結閘門；其餘封存 | Active agenda | **LOCKED 2026-09-08** |
| **OPEN pre-exdiv KD probe** | Yahoo K9/D9 · May–Jun K&lt;25 · pre-ex T−10…T−1 | Paper probe only | **OPEN 2026-09-09** |
| **ADD KD_OPT observe** | `請照順序` → 第 4 本 OPERATING | `KD_APR15_MAY15_Klt30_T15` ledger | **OPERATING 2026-09-09** |
| **OPEN EQUAL×KD mix probe** | `開 paper probe（EQUAL×KD λ-grid）` | Paper λ-grid only | **OPEN 2026-09-09** |
| **ACCEPT live cutover** | `ACCEPT` → **`KD_OPT`** | Wire `FIN_PRE_EXDIV_KD` into `e21` | **ACCEPTED 2026-09-09** |
| **OPEN autumn post-ex probe** | `開秋冬除息後低點 paper probe` | Paper Oct20–Dec10 K9 | **OPEN 2026-09-09** |
| **Autumn small-search + dual-season** | 參數小搜 + KD 雙季 mix | Paper only · stop if no lift | **STOP 2026-09-09** |

## Accepted operating posture (2026-09-09)

1. **Maintain OPERATING** paper books beside live — month-end refresh EQUAL ∥ RS ∥ MIX_L75 ∥ KD_OPT.  
2. **Live within-sleeve** = **`KD_OPT`** (`FIN_PRE_EXDIV_KD`) forward-only; Soft-Frozen **KEEP**.  
3. **Do not** — Soft-Frozen flip; E45 stitch; Telecom within-sleeve flip; history rewrite.  

## Stage results (paper)

| Stage | Best held-out score vs `FIN_EQUAL` | Verdict |
|---|---|---|
| B hard (TOP1/TOP2/MIN_LOT) | −0.112 (`FIN_MIN_LOT_PACK`) | **STOP** |
| C soft (RS / ex-div) | **+0.540** (`FIN_RS_SOFT_TILT_EXDIV`) | **CANDIDATES_LOCKED** |
| D dual-paper | `FIN_EQUAL` ∥ RS ∥ **`MIX_L75`** ∥ **`KD_OPT`** @ 500M | **OPERATING OBSERVE** |
| Mix λ-grid | **`MIX_L75`** held **+0.129** · tip YTD/1y **PASS** | **COEXIST_CANDIDATE_FOUND** |
| KD optimize | **`KD_OPT`** held **~+0.65** · tip YTD/1y **PASS** | **OPTIMAL_SELECTED_OBSERVE** |
| Live cutover | **`KD_OPT`** → `e21` | **ACCEPTED 2026-09-09** |
| Autumn post-ex probe | held **+0.422** · tip **PASS** · < live KD_OPT | **PAPER_PROBE** · no live wire |

## Still required later

| Ballot | Effect |
|---|---|
| Autumn optimize / dual-season mix (optional) | Only if human opens; **not** live cutover from this probe |
| Further FIN within-sleeve live change | Needs new ACCEPT (live already `KD_OPT`) |

## Non-ballots

| Topic | Status |
|---|---|
| Soft-Frozen clips | **KEEP** |
| Live FIN wire | **`KD_OPT` ACCEPTED 2026-09-09** (forward-only) |
| Stage B hard policies | Remain **STOP** |
| Mix / RS live wire | **NOT** selected this cycle |
| E45 stitch on this line | **FORBIDDEN** |
| EQUAL×KD_OPT mix | Paper only — not live |
| Autumn `FIN_POST_EXDIV_KD` | Paper only — **does not** replace live KD_OPT |
