# 公股＋民營並存 × MDD — Research Charter (Stage A)

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → Stage A RUNNING**  
Human: **「應該是研究公股民營並存」** · **「開公股民營並存 × MDD Stage-A charter 並開始跑」**  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Live Soft-Frozen: **KEEP** 3-sleeve FINBAND `[0.60, 0.90]` · 公股 R1 · `KD_OPT` · `TEL_EQUAL`  
Capital **500M** · lot **1000** · Exact T+1 · E22 on extended pub+priv panel  

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257` priv-replace.**

---

## Problem

Prior Stage A on 並存 **STOP** under the old score (`MDD↑ − 0.5·|CAGR giveback|`):

| Prior track | Verdict | Note |
|---|---|---|
| Dollar-split dual (`FIN_PUB_PRIV_DUAL_SLEEVE`) | STOP | CAGR↑ / MDD↓ |
| Soft-Frozen 4-sleeve clips | STOP | 0 coexist · FinPriv raises MDD |
| PRIV-replace / ALL12 | STOP | vs `LIVE_PUB_KD` |

Cutover PRE/POST compare showed **priv-replace** lifts tip CAGR but **worsens sealed/heldout MDD**.  
Human direction: research **公股＋民營並存**, not replace — with **MDD recover vs 公股 baseline** as the primary question.

Target live image (research only):

| Sleeve | Members |
|---|---|
| **FinPub** | 2880 2886 2892 5880 |
| **FinPriv** | 2884 2885 2890 2891 2881 2882 |
| **Telecom** | 2412 3045 4904 |
| **0050** | 0050 |

## Contrast

| Design | Topology | This charter |
|---|---|---|
| `#257` priv live | 3-sleeve; **swap** FIN → 民營 | **Out of scope** (replace) |
| Dollar-split dual | 3-sleeve Soft-Frozen; split FIN dollars | **In** (mechanism A) |
| 4-sleeve clips | FinPub+FinPriv+TEL+0050 | **In** (mechanism B) |

## In scope (Stage A — paper)

1. Baseline: **`LIVE_PUB_KD`** (live-intent 公股 Soft-Frozen + KD).  
2. Mechanisms (both, predeclared):  
   - **A** dollar-split `FIN_DUAL_PUB_PRIV` (high `pub_share` bias for MDD)  
   - **B** compact Soft-Frozen 4-sleeve clip grid (small FinPriv boxes)  
3. Within-sleeve: FinPub=`KD_OPT`; FinPriv ∈ `{EQUAL, KD_OPT}` (公股 calendar KD probe).  
4. Sealed **and** held-out MDD are **hard gates** (not report-only).  
5. Soft-Frozen live constants / `e21` untouched.

## Objective (predeclared)

Windows: **heldout_2019_plus** + **sealed_2023_plus** (both gate) · tip YTD/1y observe.

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required):

1. `tip_clean` — YTD + trailing_1y CAGR tip gates PASS (same thresholds as prior screens)  
2. `tip_mdd_ok` — YTD and 1y MDD↑ ≥ **−0.5 pp** vs baseline (tolerance)  
3. `heldout_mdd_improve_pp ≥ 0`  
4. `sealed_mdd_improve_pp ≥ 0`  
5. `heldout CAGR giveback_pp ≤ 3.0`  
6. `score_mdd > 0`

## Search space (predeclared — do not expand after peek)

### Mechanism A — dollar-split

| Axis | Values |
|---|---|
| `pub_share` | `{0.90, 0.85, 0.80, 0.75}` |
| FinPriv within | `{EQUAL, KD_OPT}` |

### Mechanism B — 4-sleeve (TEL/ETF clips = live Soft-Frozen)

| Axis | Values |
|---|---|
| FinPub clip | `[0.60, 0.90]` only |
| FinPriv clip | `[0.00, 0.15]` · `[0.00, 0.20]` · `[0.05, 0.20]` · `[0.05, 0.25]` |
| `prior_priv_frac` | `{0.10, 0.15}` |
| FinPriv within | `{EQUAL, KD_OPT}` |

Hard filters: floors sum ≤ 1; FinPriv width ≥ 0.15 except control.

**Controls**

- `LIVE_PUB_KD` — baseline  
- `SF4_CTRL_PUB_ONLY` — FinPriv clip `[0,0]`, `prior_priv_frac=0` (machinery sanity)

## Out of scope / WON’T

- Edit `e16_soft_frozen_base.py` live constants  
- Live `e21` universe expand / priv-replace promote  
- Retune grid after sealed peek  
- Bundle Class D Soft-Frozen flip with Stage A  
- Broker live-write  
- FUSE/BLEND/L4/DH stack in this Stage A (baseline stays Soft-Frozen live-intent; stack compose = later charter if Stage A clears)

## Stage plan

| Stage | Action | Exit |
|---|---|---|
| **A** | Run predeclared grid · write rescreen + decision pack | Coexist → candidates; else STOP |
| **B** | Dual-paper observe on winners only (if any) | Separate ballot |
| **D** | Soft-Frozen / live cutover | Human ACCEPT only |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/e16_pub_priv_coexist_mdd_stage_a.py
```

Artifacts: `research/ops/PUB_PRIV_COEXIST_MDD_*` · `repro/pub-priv-coexist-mdd-stagea/`

## Label

`PUB_PRIV_COEXIST_MDD_CHARTER_2026-09-19__STAGE_A`
