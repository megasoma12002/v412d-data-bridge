# 金融公 / 金融民 Dual-Sleeve — Research Charter

Date: 2026-09-09  
Status: **CHARTER ACCEPTED → Stage A STOP** — human **「應該策略要把金融分成 金融公 金融民」** · pack `FIN_PUB_PRIV_DUAL_SLEEVE_DECISION_PACK.md`  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP FINBAND [0.60, 0.90]** (3-sleeve SSOT unchanged this Stage)  
Live FIN within: **KD_OPT KEEP** (公股) · Telecom **TEL_EQUAL KEEP**  
Capital **500M** · lot **1000** · Exact T+1 · E22 with private div/adj filled

**Passing ≠ Soft-Frozen flip ≠ live 4-sleeve cutover.**

---

## Problem

Prior Stage A (`PRIVATE_FIN_HOLDINGS`) **replaced** Soft-Frozen Financial names with 民營 / ALL12  
inside the **same** Financial weight → STOP (MDD drag).

Human direction: strategy should treat Financial as **two coexist sleeves**:

| Sleeve | Label | Codes | Within (Stage A) |
|---|---|---|---|
| **金融公** | PUB_R1 | 2880 2886 2892 5880 | `KD_OPT` (live) |
| **金融民** | PRIV_R3R4 | 2884 2885 2890 2891 2881 2882 | EQUAL or `KD_OPT` probe |

Soft-Frozen **Financial weight** from FINBAND stays one band; Stage A only **splits dollars**  
`pub_share · W_fin` → 公股, `(1−pub_share) · W_fin` → 民營.

Router features remain Soft-Frozen **公股-only** (do not retrain Soft-Frozen on 民營 returns this Stage).

## Contrast

| Design | What happens to 公股 |
|---|---|
| PRIV-replace (prior STOP) | Dropped from Financial sleeve |
| Dual-sleeve (this charter) | Kept; 民營 added alongside via dollar split |

## In scope (paper)

1. Grid `pub_share` ∈ {1.0, 0.85, 0.75, 0.60, 0.50}  
2. 公 within = `FIN_PRE_EXDIV_KD` (KD_OPT); 民 within = EQUAL ∥ KD_OPT  
3. Baseline `LIVE_PUB_KD`; metrics held-out score · tip YTD/1y · sealed report-only  
4. Policy id `FIN_DUAL_PUB_PRIV` in `within_sleeve_alloc` / `e50.simulate_core` (paper kwargs)

## Out of scope / WON’T

- Live Soft-Frozen → 4-sleeve rewrite this PR  
- Live e21 universe expand without dedicated ACCEPT  
- Soft-Frozen feature rebuild on 民營 sleeve returns (Stage B+)  
- Replacing PRIV-replace STOP narrative (different question)

## Stage plan

```
A  Charter + dollar-split grid @ 500M     ← this PR
B  If tip-clean + held-out>0 → dual-paper observe
C  Soft-Frozen 4-sleeve / live cutover ONLY after dedicated ACCEPT
```

## Artifacts

- `scripts/e16_fin_pub_priv_dual_sleeve.py`
- `research/ops/FIN_PUB_PRIV_DUAL_SLEEVE_CHARTER.md`
- `research/ops/FIN_PUB_PRIV_DUAL_SLEEVE_RESCREEN.{md,json}`
- `repro/fin-pub-priv-dual-sleeve-20260909/`

## Label

`FIN_PUB_PRIV_DUAL_SLEEVE_CHARTER_2026-09-09__PAPER_DOLLAR_SPLIT`
