# FIN×SAT tip-gap 週期預測／特徵 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_MDD_ONLY`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9h 週期切換 **`TIP_MDD_ONLY`** — ZigZag／regime／月季未對齊 tip HARD 拖累
- 0k9g 年聚合有誤導 · oracle 年切不可用
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 研究 tip-gap／週期缺口如何預測或找特徵 · 方法不限 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_TIPGAP_PRED_STAGEA_CHARTER_2026-09-28__DONE_TIP_MDD_ONLY__NO_LIVE_WIRE`

## Why

Binding failure 一直是 **tip CAGR−**（COMP HARD 拖累），不是 held。  
Belief: 缺口是「**tip-drag 片段**何時發生」——可用多方法找 **領先特徵／週期對齊度**，再決定下一輪切換定義。  
Risk: 僅同期相關無領先力；或 tip 窗口樣本太短。

## Methods (open, finite report)

1. **Gap labeling** — forward／trailing COMP−SAT 相對報酬；標 SAT-lead 日／月  
2. **Tip-window contrast** — YTD & trailing_1y vs held：特徵均值差  
3. **Leading IC** — lag-1 特徵 × forward_21d (rc−rs) 相關／符號命中率（預註冊特徵表）  
4. **Cycle overlap** — ZigZag／Crisis／月 REL 狀態與 tip-drag 日重疊率  
5. **Fill intensity** — COMP SELL 密度（HARD 代理）是否領先 tip-gap  
6. **Probe switches** — 僅對 IC 過門的預註冊特徵做 ≤3 條 lag-1 切換試探（非 peek 擴網）

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 年切 oracle 當候選 | **FORBIDDEN** |
| 特徵表外再擴門檻／再挖 IC | **FORBIDDEN**（本包內一次掃描） |
| Live wire | **forbidden** |

## Pre-registered feature table (IC scan)

| feat | type |
|---|---|
| `crisis_l1` / `bearcrisis_l1` | regime |
| `zz08_bear_l1` / `zz12_bear_l1` | cycle |
| `mdd0050_63_l1` / `r0050_63_l1` / `vol0050_21_l1` | 0050 |
| `trail_rel_21_l1` / `trail_rel_63_l1` | COMP−SAT momentum |
| `comp_sells_21_l1` | COMP fill SELL count 21d |
| `month_sin_l1` / `month_cos_l1` | seasonality |

IC gate for probe: \|IC\| ≥ **0.04** 且 sign-hit ≥ **52%** → 最多 3 條 probe switch。

## Probe HIT gates (same as prior)

tip-clean + held CAGR↑≥+0.10 + vs SAT +0.05 · `switch` only.

## Verdicts

| Verdict | Meaning |
|---|---|
| `GAP_PRED_HIT` | ≥1 probe switch HIT |
| `GAP_FEAT_READY` | ≥1 feat clears IC gate；probe 未 HIT／無 probe |
| `GAP_FEAT_WEAK` | tip contrast 可見但無 feat 過 IC gate |
| `TIP_MDD_ONLY` / `NO_PRED` | as labeled |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tipgap_pred_stagea.py
```

Register: **0k9i**
