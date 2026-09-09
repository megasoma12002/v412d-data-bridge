# Telecom Within-Sleeve — Async Split Research (FIN-parallel)

Date: 2026-09-09  
Status: **CHARTER DONE · RESEARCH STOP** — human **「電信三檔也做跟金融股一樣拆開的研究」**  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP [0.60, 0.90] FINBAND**  
Live FIN within-sleeve: **KD_OPT KEEP** (held fixed to isolate Telecom)  
Live Telecom: **TEL_EQUAL** until dedicated cutover ACCEPT  
Capital **500M** · lot **1000** · books **`E22_v2s_tw`**

**Passing ≠ Soft-Frozen flip ≠ live cutover.**

---

## Problem

Telecom sleeve (3 names: 2412 / 3045 / 4904) is still **equal-split** on live.  
Financial already has async within-sleeve live **`KD_OPT`** (season KD tilt + pre-ex skip-buy).  
Human asks for the **same split research** on Telecom: per-name timing, not only lot-packing.

Prior Telecom lines (still valid evidence):

| Stage | Result |
|---|---|
| B hard TOP/MIN_LOT @ 3M | **STOP** (no positive held-out vs EQUAL) |
| C pack optimize @ 500M | `TEL_DIVERSIFY_PACK` / `TEL_SCORE_LOT_PACK` beat EQUAL |

This charter adds **FIN-parallel Stage D timing** + optional **PRE_EXDIV_KD** grid (Telecom cash-ex mostly **Jun–Aug**).

## In scope

1. Paper policies for within-Telecom async allocation @ **500M / 整張**.  
2. Soft-Frozen sleeve targets unchanged (live FINBAND SSOT).  
3. Financial held at live **`FIN_PRE_EXDIV_KD` / KD_OPT** (isolate TEL).  
4. Compare vs `TEL_EQUAL` BASE: held-out score + tip YTD/1y gates.

## Out of scope / WON’T

- Soft-Frozen clip edit  
- Live `e21` Telecom wire without dedicated ACCEPT  
- Changing live FIN KD_OPT in this research  
- Zero-lot continuous-book orders  

## Predeclared policies (Stage D — per-name timing)

| id | Rule sketch |
|---|---|
| `TEL_EQUAL` | Equal split 3 names (BASE) |
| `TEL_RS_SOFT_TILT` | Buy $ soft-tilt by causal mom score |
| `TEL_EXDIV_SKIP_BUY` | Skip buy on cash/stock ex-date for that name |
| `TEL_RS_SOFT_TILT_EXDIV` | Soft-tilt among non-exdiv names |
| `TEL_MIX_EQUAL_RS_EXDIV` | λ=0.75 EQUAL + (1−λ) RS_EXDIV (FIN MIX_L75 analogue) |
| `TEL_PRE_EXDIV_KD` | Yahoo K9 season tilt + pre-ex T−N…T0 skip-buy (grid) |

Selection: **held-out 2019+**  
Score: `MDD_improve_pp − 0.5 × |CAGR_giveback_pp|` vs `TEL_EQUAL`  
Tip: YTD / trailing_1y giveback gates (PASS / ALERT / PAUSE).

## Stage plan

```
D1  Timing screen (RS / EXDIV / combo / MIX_L75-analogue)   ← this PR
D2  TEL_PRE_EXDIV_KD small-grid (summer seasons)           ← this PR
E   Dual-paper observe OPEN (only if tip-clean + score>0)  ← later ballot
F   Live Telecom cutover ACCEPT (separate)                 ← later ballot
```

## Artifacts

- `scripts/e16_telecom_within_sleeve_stage_d.py`
- `scripts/e16_telecom_pre_exdiv_kd_optimize.py`
- `research/ops/TELECOM_WITHIN_SLEEVE_ASYNC_STAGE_D.md`
- `research/ops/TELECOM_PRE_EXDIV_KD_OPTIMIZE.md`
- `repro/telecom-within-sleeve-async-20260909/`
- `repro/telecom-pre-exdiv-kd-optimize-20260909/`

## Label

`TELECOM_WITHIN_SLEEVE_ASYNC_CHARTER_2026-09-09__FIN_PARALLEL__PAPER_ONLY`
