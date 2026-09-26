# 大盤下行 → 00632R — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **CHARTER OPEN → Stage A** · Soft-Frozen live **KEEP** · live wire **false**  
Human: **「00632R是在大盤下行時有用」**  
Parent fails: COOL-dwell / COOL-pulse / FUSE Soft-sell → CAGR↓ or MDD_BLOCK

## Thesis

`00632R`（台50反1）經濟含義是 **大盤下行受益**。  
Prior gates（COOL 縮倉、Soft-sell 過熱）**≠** 大盤下行，易雙重避險或錯邊。  
This charter gates DEF **only on market-down sensors**.

## Live twin (unchanged)

Soft-Frozen F[0.60,0.80] E[0.00,0.50] + FUSE Soft+Sleeve + `COOL_c8` · capital 500M · Exact T+1.

## Sensors (predeclared — do not expand after peek)

Using **0050** adj_close (台50 proxy; causal):

| ID | 大盤下行定義 |
|---|---|
| `RET5_M3` | 5日報酬 ≤ **−3%** |
| `RET5_M5` | 5日報酬 ≤ **−5%** |
| `DD20_M5` | 相對 20日高點回撤 ≤ **−5%** |
| `DD20_M8` | 相對 20日高點回撤 ≤ **−8%** |

While sensor True（且 `00632R` listed）：`DEF = α × 0.25`；False → DEF=0（賣出）。  
α ∈ `{0.50, 1.00}`。  
Equity sleeves = live FUSE targets × COOL（同 baseline）。

## Objective

tip OK · held MDD↑ ≥ −0.25 · sealed MDD↑ ≥ 0 · held CAGR↑ ≥ +0.20.

| Verdict | Meaning |
|---|---|
| `MKTDOWN_INV_HIT` | ≥1 coexist |
| `MKTDOWN_INV_SOFT` | MDD/tip OK, CAGR short |
| `MDD_BLOCK` / `NO_LIFT` | as named |

Even HIT → paper observe only.

## Non-actions

No COOL/FUSE retune · Soft-Frozen KEEP · no tip `00632R` without Class D.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/mktdown_t50_inv_stagea.py
```

Label: `MKTDOWN_T50_INV_CHARTER_2026-09-25__STAGE_A_OPEN`
