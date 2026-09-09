# 民營金控 Native Within-Sleeve — Research Charter

Date: 2026-09-09  
Status: **CHARTER ACCEPTED → OPTIMAL_SELECTED** — human **「民營的策略再研究一下畢竟跟公股的習性不一樣」** · pack `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md` · observe OPEN
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP** 3-sleeve FINBAND · Financial membership **公股 R1 KEEP**  
Live FIN within: **KD_OPT KEEP** (公股) · Telecom **TEL_EQUAL KEEP**  
Capital **500M** · lot **1000** · Exact T+1 · E22 (private div/adj filled)

**Passing ≠ Soft-Frozen flip ≠ live universe expand ≠ 4-sleeve cutover.**

---

## Problem

Prior 民營 work transplanted **公股** tools:

| Prior | What was wrong for 民營 |
|---|---|
| PRIV-replace / dual / 4-sleeve | Used 公股 `KD_APR15_MAY15` or EQUAL; asked stack-level questions |
| Cash ex calendar | **公股 ≈ Aug** · **民營 ≈ Jun–Jul** (2019+: Jul dominant) |

Human: 民營習性不同 → research **民營-native** within-sleeve policies on PRIV_R3R4, not Soft-Frozen topology.

## Universe

| Label | Codes |
|---|---|
| **PRIV_R3R4** | 2884 玉山 · 2885 元大 · 2890 永豐 · 2891 中信 · 2881 富邦 · 2882 國泰 |

Soft-Frozen **sleeve weights** still from live FINBAND (公股 features).  
Paper books: Financial dollars → **PRIV only** (same harness as PRIV Stage A).

## In scope

1. Baseline **`PRIV_EQUAL`** (within-民營 equal-split).  
2. Anchor: transplanted 公股 **`KD_OPT`** (`APR15_MAY15_Klt30_T15`) on PRIV.  
3. Native **`FIN_PRE_EXDIV_KD`** grid with seasons biased to **May–Jul** (pre Jun–Jul ex).  
4. Anchors: `FIN_RS_SOFT_TILT_EXDIV` · `MIX_EQUAL_PRE_EXDIV_KD` λ=0.75.  
5. Objective vs `PRIV_EQUAL` (held-out): tip-clean + score>0 → coexist; sealed report-only.  
6. Report-only cross-check vs `LIVE_PUB_KD` (does **not** select winners).

## KD search space (predeclared)

| Axis | Values |
|---|---|
| Season | `APR15_MAY15` (transplant) · `MAY` · `MAY15_JUN15` · `MAY15_JUN30` · `JUN` · `JUN01_JUL15` · `MAY15_JUL15` |
| K thresh | `{20, 25, 30}` |
| Pre-ex days | `{5, 10, 15}` |
| Active score | `1.5` (fixed) |

## Out of scope / WON’T

- Soft-Frozen membership / 4-sleeve Class D flip this PR  
- Live e21 expand to 民營  
- Retune after sealed peek  
- Claiming 民營 beats 公股 live from within-sleeve alone  

## Stage plan

```
A  Charter + native KD grid + anchors vs PRIV_EQUAL   ← this PR
B  If tip-clean + held-out>0 → dual-paper observe ballot
C  Any live / Soft-Frozen topology use needs separate ACCEPT
```

## Artifacts

- `research/ops/FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER.md`
- `scripts/e16_fin_priv_native_optimize.py`
- `research/ops/FIN_PRIV_NATIVE_WITHIN_SLEEVE_OPTIMIZE.{md,json}`
- `repro/fin-priv-native-20260909/`

## Label

`FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER_2026-09-09__JUN_JUL_EXDIV`
