# FIN_SAT_SWITCH_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:10:09Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_SWITCH_STAGEA_CHARTER.md`
Screen: `FIN_SAT_SWITCH_STAGEA_SCREEN.md`
Parents: 0k9e blend TIP_MDD_ONLY · COMPOSITE observe · SAT_A20_RELAX observe · register **0k9f**

## Verdict

**`TIP_MDD_ONLY`**

SAT parent held CAGR↑ = 0.3343pp · switch must clear tip-clean + held≥+0.10 + vs SAT ≥+0.05.

No switch cleared tip-clean economic gates.

## Diagnosis

Short REL (21/63) lifts held CAGR well above SAT (+0.87～+1.17) and stays tipMDD↑, but still tip CAGR− (−5pp) — switch does not fully exit COMP tip drag.  
Long REL126 is the only tip-clean switch (tipCAGR↑ YTD +0.68) but held MDD↑ −0.58 fails economic (−0.25).  
DD63 and hysteresis do not open a HIT. Feasible region still empty under this finite lag-1 grid.

- `SW_REL21_CDEF` · %SAT=48.65 flips=409 · heldCAGR↑ 0.8699 tipCAGR↑ -5.5106 · tipClean=False econ=True vsSAT=True
- `SW_REL63_CDEF` · %SAT=47.01 flips=191 · heldCAGR↑ 1.1698 tipCAGR↑ -5.1372 · tipClean=False econ=True vsSAT=True
- `SW_REL126_CDEF` · %SAT=48.77 flips=149 · heldCAGR↑ 0.9199 tipCAGR↑ 0.6801 · tipClean=True econ=False vsSAT=True
- `SW_REL63_SDEF` · %SAT=48.92 flips=190 · heldCAGR↑ 1.1698 tipCAGR↑ -5.1372 · tipClean=False econ=True vsSAT=True
- `SW_DD63_CDEF` · %SAT=49.12 flips=83 · heldCAGR↑ -0.0341 tipCAGR↑ -7.8587 · tipClean=False econ=False vsSAT=False
- `SW_REL63_H21` · %SAT=46.81 flips=67 · heldCAGR↑ 1.9581 tipCAGR↑ -5.5348 · tipClean=False econ=False vsSAT=True

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not reopen HARD×α / COOL-HARD / blend weight grids from this pack
4. Even HIT → paper observe ballot DRAFT only · no live wire

Label: `FIN_SAT_SWITCH_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
