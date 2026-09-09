# Soft-Frozen 4-Sleeve (金融公 / 金融民) — Research Charter

Date: 2026-09-09  
Status: **CHARTER ACCEPTED → Stage A STOP** — human **「做成 Soft-Frozen 四條 sleeve（公／民各自 clip），另開 charter」** · pack `SOFT_FROZEN_4SLEEVE_DECISION_PACK.md`  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen live flip = **Class D** later only  
Live Soft-Frozen: **KEEP** 3-sleeve FINBAND `[0.60, 0.90]` / TEL `[0.03, 0.35]` / 0050 `[0.00, 0.35]`  
Live FIN within: **KD_OPT KEEP** · Telecom **TEL_EQUAL KEEP**  
Capital **500M** · lot **1000** · Exact T+1 · E22 (private div/adj filled)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite.**

---

## Problem

Dollar-split Stage A (`FIN_PUB_PRIV_DUAL_SLEEVE`) kept **one** Soft-Frozen Financial band and only split dollars → **STOP** (CAGR↑ / MDD↓).

Human wants Soft-Frozen itself to become **four sleeves** with **independent clips**:

| Sleeve | Members | Role |
|---|---|---|
| **FinPub** 金融公 | 2880 2886 2892 5880 | Soft-Frozen 公股 core |
| **FinPriv** 金融民 | 2884 2885 2890 2891 2881 2882 | Independent private sleeve |
| **Telecom** | 2412 3045 4904 | Unchanged |
| **0050** | 0050 | Unchanged |

Router features/scores run **per sleeve** (FinPub return ≠ FinPriv return). Clips bind each sleeve separately (not a fixed `pub_share` of one Financial weight).

## Contrast

| Design | Soft-Frozen topology | Result so far |
|---|---|---|
| PRIV-replace | 3-sleeve; swap FIN names | STOP |
| Dollar-split dual | 3-sleeve; split FIN dollars | STOP |
| **4-sleeve clips (this)** | FinPub+FinPriv+TEL+0050 | Stage A running |

## In scope (Stage A — paper)

1. Challenger module **outside** `e16_soft_frozen_base.py` (live SSOT untouched).  
2. Predeclared FinPub / FinPriv clip grid; TEL/0050 clips **frozen at live Soft-Frozen**.  
3. Regime priors: split legacy Financial prior mass with `prior_priv_frac` ∈ predeclared set.  
4. Within-sleeve: FinPub=`KD_OPT`, FinPriv=`EQUAL` (primary); optional FinPriv=`KD_OPT` probe.  
5. Baseline: live-intent **`LIVE_PUB_KD`** (3-sleeve Soft-Frozen + 公股 KD).  
6. Objective (held-out 2019+, vs baseline):  
   `score = MDD_improve_pp − 0.5 × |CAGR_giveback_pp|`  
   Coexist = tip-clean (YTD+1y PASS) **and** score > 0.  
7. Sealed 2023+ = **report only** (not for selection).

## Search space (predeclared — do not expand after peeking)

Coordinate: `(FinPub_lo, FinPub_hi, FinPriv_lo, FinPriv_hi, prior_priv_frac)`  
TEL/ETF clips fixed: live Soft-Frozen.

| Axis | Values |
|---|---|
| FinPub clip | `[0.50,0.85]` · `[0.55,0.90]` · `[0.60,0.90]` |
| FinPriv clip | `[0.00,0.20]` · `[0.05,0.25]` · `[0.10,0.30]` · `[0.00,0.30]` |
| `prior_priv_frac` | `{0.15, 0.25}` — fraction of legacy Financial **regime prior** assigned to FinPriv |

Hard filters:

- `hi − lo ≥ 0.10` for FinPub; `hi − lo ≥ 0.15` for FinPriv (except exact `[0,0]` control only)  
- `FinPub_lo + FinPriv_lo + TEL_lo + ETF_lo ≤ 1`  
- Exclude degenerate FinPriv `[0,0]` from winner pool (optional **4MAP_LIVE** control only)

**Control books**

- `LIVE_PUB_KD` — current live intent (3-sleeve)  
- `SF4_CTRL_PUB_ONLY` — 4-sleeve machinery with FinPriv clip `[0,0]`, FinPub `[0.60,0.90]`, `prior_priv_frac=0` (sanity vs live)

## Out of scope / WON’T

- Edit live constants in `e16_soft_frozen_base.py` this PR  
- Live `e21` universe / clip cutover without dedicated Class D ACCEPT  
- Retune grid after sealed peek  
- Bundle Soft-Frozen flip with Stage A search in one PR  
- Soft-Frozen feature rebuild that drops 公股 regime/TAIEX rules

## Stage plan

```
A  Charter ACCEPT + finite clip grid @ 500M     ← this PR
B  If tip-clean + held-out>0 → dual-paper observe ballot
C  Class D Soft-Frozen 4-sleeve cutover ONLY after dedicated ACCEPT
```

## Artifacts

- `research/ops/SOFT_FROZEN_4SLEEVE_CHARTER.md` (this file)  
- `scripts/e16_soft_frozen_4sleeve.py` (challenger router)  
- `scripts/e16_soft_frozen_4sleeve_stage_a.py` (grid runner)  
- `research/ops/SOFT_FROZEN_4SLEEVE_STAGE_A.{md,json}`  
- `repro/soft-frozen-4sleeve-20260909/`

## Label

`SOFT_FROZEN_4SLEEVE_CHARTER_2026-09-09__PAPER_FINPUB_FINPRIV_CLIPS`
