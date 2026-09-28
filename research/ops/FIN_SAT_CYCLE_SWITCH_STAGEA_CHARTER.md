# FIN×SAT 週期互斥切換 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9g 互斥特徵 **`TIP_MDD_ONLY`** — 年切 oracle 有上界，但年切不可實作；日頻 lag-1 未對齊 tip
- 0k9e／0k9f blend／REL 皆 `TIP_MDD_ONLY`
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 以週期（峰谷／regime confirm／月季）抓 COMP↔SAT 互斥 · 非年切 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_CYCLE_SWITCH_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

0k9g 證明互斥在 **Bull↔Crisis** 層真實，且 **年 oracle** 有 HIT 上界——但年切是 lookahead／日曆假週期。  
Belief: 改用 **市場週期**（0050 峰谷半週期、regime 確認片段、月／季 rel 再平衡）才能因果抓住同一互斥。  
Risk: 週期定義錯頻（太慢仍吃 tip；太快抖動）；或僅 DIAG 無 HIT。

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 年切 oracle 當候選／peek 後改門檻 | **FORBIDDEN** |
| 再開 blend weight／REL grid／HARD×α | **FORBIDDEN** |
| Live wire | **forbidden** |

## Mechanism

Frozen parent NAVs · lag-1 causal · 每日擇一 COMP 或 SAT（非加權）。

週期定義（預註冊）：

| Family | Cycle |
|---|---|
| ZigZag half-cycle | 0050 峰↔谷振幅 thr∈{8%,12%}：峰→谷 = SAT；谷→峰 = COMP |
| Regime confirm | Crisis（或 Bear\|Crisis）連續 K=5 日才進 SAT；離開確認 K=5 |
| Month / Quarter rel | 月末／季末比較 trail rel；整段下個週期持有勝方 |

Diag only: episode-level COMP−SAT 表（非年）· **禁止** year-oracle 當 HIT。

## Gates (HIT) — `switch` family

1. tip YTD & 1y **CAGR↑ ≥ 0** 且 **MDD↑ ≥ 0**  
2. held CAGR↑ ≥ **+0.10pp** · held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. held CAGR↑ ≥ SAT held + **+0.05pp**

## Grid (finite ≤9)

| ID | fam | rule |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live base |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `SW_ZZ08_BEAR_SAT` | switch | ZigZag 8% · bear-half SAT |
| `SW_ZZ12_BEAR_SAT` | switch | ZigZag 12% · bear-half SAT |
| `SW_CRISIS_K5` | switch | Crisis confirm K=5 |
| `SW_BEARCRISIS_K5` | switch | Bear\|Crisis confirm K=5 |
| `SW_MONTH_REL63` | switch | month-end REL63 → next month pick |
| `SW_QTR_REL126` | switch | quarter-end REL126 → next quarter pick |

## Verdicts

| Verdict | Meaning |
|---|---|
| `CYCLE_HIT` | ≥1 `switch` clears HIT |
| `TIP_CLEAN_SOFT` / `TIP_MDD_ONLY` / `TIP_BLOCK` / `NO_EDGE` / `DIAG_ONLY` | as labeled |

Even HIT → observe ballot **DRAFT only** · parents KEEP · no live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_cycle_switch_stagea.py
```

Register: **0k9h**
