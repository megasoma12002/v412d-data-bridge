# Soft-Frozen 四類 + DH／L4 防禦 × MDD — Research Charter (Stage A)

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → Stage A STOP** (`STAGE_A_SCORE_POS_GATES_FAIL` — defence improves heldout／tip but sealed MDD still < 0)  
Human: confirm 公／民各成一類（四 sleeve）· next **「新機制（四類 + DH/L4 防禦）」**（不改 sealed 目標、不重調舊 clip 格）  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live flip = **Class D** later only  
Prior STOP: `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md`（raw 四類／dual-split · **0 sealed-MDD coexist**）  
Live Soft-Frozen: **KEEP** 3-sleeve 公股 · capital **500M** · lot **1000** · Exact T+1  

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite.**

---

## Problem

Raw 四類（FinPub／FinPriv／TEL／0050）Stage A cleared tip／often heldout MDD, but **every** priv-bearing book failed **sealed MDD↑ ≥ 0**.

Human topology is still **四類**（不是 priv-replace、不是只拆 Financial 錢）。  
New question: can **defence actuators** on a **frozen** 四類 cell repair sealed MDD without retuning FinPriv clips?

## Frozen offense cell (do not retune)

From prior Stage A best priv-bearing book:

| Param | Value |
|---|---|
| FinPub clip | `[0.60, 0.90]` |
| FinPriv clip | `[0.00, 0.15]` |
| `prior_priv_frac` | `0.10` |
| FinPub within | `KD_OPT` |
| FinPriv within | `KD_OPT` |
| Label | `SF4_P60-90_V0-15_F10_KD` |

Defence reference book (FinPriv off): `SF4_CTRL_PUB_ONLY` (FinPriv clip `[0,0]`, prior_frac `0`).

## New mechanism (predeclared)

| Book | Mechanism |
|---|---|
| `LIVE_PUB_KD` | Baseline — live-intent 3-sleeve 公股 |
| `SF4_OFFENSE` | Frozen 四類 cell (no defence) — expect sealed fail (sanity) |
| `SF4_DH` | Offense + **DH_dd06** (SHRINK 0.50; exposure from offense NAV) |
| `SF4_L4_08` | Offense → on TAIEX DD≤**−8%**, path-switch to `SF4_CTRL_PUB_ONLY` weights |
| `SF4_L4_10` | Same with DD≤**−10%** |
| `SF4_L4_08_DH` | L4_08 path then DH on that offense NAV |
| `SF4_L4_10_DH` | L4_10 path then DH |

Notes:

- `e50` `e45_exposure` **unsupported** with FinPub/FinPriv targets → DH applied by **scaling sleeve weights** (residual = cash).  
- L4 here = **path switch 四類→公股-only 四類機器**, not FIN_CAP_50 3-sleeve L4.

## Objective (unchanged from MDD charter)

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok (≥ −0.5 pp) · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · heldout CAGR gb ≤ 3.0 · score_mdd > 0.

## Out of scope / WON’T

- Retune FinPub／FinPriv clip grid after sealed peek  
- Soften sealed MDD gate  
- Priv-replace live (`#257`)  
- Edit `e16_soft_frozen_base.py`  
- Live e21 wire / Class D flip from Stage A  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/e16_sf4_defence_mdd_stage_a.py
```

## Label

`SF4_DEFENCE_MDD_CHARTER_2026-09-19__STAGE_A`
