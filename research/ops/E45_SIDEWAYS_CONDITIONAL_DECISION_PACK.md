# E45 Sideways-Conditional — Decision Pack

Date: 2026-09-08  
Status: **RESEARCH DONE — residue closed (no Soft_A beater)**  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged

## Question

After Soft_A mult grid, are **conditional Sideways** rules still experimentable for tip PASS + held-out > Soft_A?

## Result

All six conditionals tip-clean; **none** beat Soft_A (+0.829).

| Book | Held-out | vs Soft_A |
|---|---:|---|
| Soft_A | **+0.829** | — |
| SIDE_MAX20 | +0.829 | ≈ Soft_A (cap never binds much) |
| SIDE_MAX10 | +0.795 | worse |
| SIDE_DD05 | +0.320 | worse |
| SIDE_HIGH_S80 / CONT / DD10 | ≤ +0.23 | worse |

## Binding read

1. Sideways **constant mult** and **conditional open** residue → closed for beating Soft_A while tip-clean.  
2. Tip vs long-score tradeoff remains operational (Soft_A / dual-monitor / ACCEPT tradeoff) — not another Sideways knob.  
3. Further score chase needs **new sensor/data**, not Soft-Frozen Sideways rules on C35.

Artifacts: `E45_SIDEWAYS_CONDITIONAL_RESEARCH.md` · freeze · `scripts/e45_sideways_conditional_paper.py`
