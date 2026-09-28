# FIN×SAT tip-lead 決策點 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `LEAD_SIGNAL`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9n 局部互斥 **`TIP_LAG_BLOCK`** — tip/held 時段分離；UB tip-clean+held；lag-1 擋 HIT
- 0k9m/0k9l · COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 在局部互斥＋TIP_LAG_BLOCK 下，找出可領先 SAT_LEAD 進入／退出的決策點，讓 Exact T+1 仍可能 tip-clean · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_CHARTER_2026-09-28__DONE_LEAD_SIGNAL__NO_LIVE_WIRE`

## Why

0k9n：結構可解（UB），binding = **lag**。  
Belief: SAT_LEAD **進入／退出日** 前後有可觀測 lead（crisis／SELL／0050／trail 斜率），可定義決策點使 lag-1 仍蓋住 tip 損害。  
Risk: lead IC 弱或提早進 SAT 傷 held MDD。

## Diagnosis（預註冊）

- Label `enter` = SAT_LEAD run 起點；`exit` = run 終點次日  
- Lead k=1..5：特徵 `t−k` → `enter_t` 的 IC／sign-hit／lift  
- Pre-enter 窗 (−5..−1) 特徵均值 vs 基線  
- 特徵集（既有，不擴表）：`crisis, bearcrisis, r0050_63, mdd0050_63, vol0050_21, comp_sells_21, zz08_bear, trail_rel_63, trail_slope_5`

## Books

| ID | fam | 規則 |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `UB_ENTER_M1` | ub | 進場日提前 1 日的 oracle SAT_LEAD（**非因果**） |
| `UB_STATE_SD` | ub | 同日 SAT_LEAD（0k9n 對照） |
| `R_SAT_LEAD_L1` | switch | lag-1 SAT_LEAD（baseline） |
| `R_HALF_THETA_L1` | switch | `trail_rel_63_l1 ≤ −0.005` |
| `R_SLOPE_EARLY_L1` | switch | `trail_l1 < trail_l6 ≤ 0` ∧ `trail_l1 ≤ −0.005` |
| `R_CONF_EARLY_L1` | switch | 進：`(crisis∨sells_hi)_l1 ∧ trail_l1<0`；出：`trail_l1≥0`；min-hold 5 |
| `R_LEAD_OR_STATE_L1` | switch | `SAT_LEAD_l1 ∨ (crisis_l1 ∧ trail_l1≤−0.005)` |

## Gates (HIT)

`switch` only · tip-clean + held CAGR↑≥+0.10 + vs SAT +0.05。UB 只計 `ub_shaped`。

## Verdicts

`LEAD_HIT` / `LEAD_SIGNAL` / `TIP_LAG_BLOCK` / `TIP_MDD_ONLY` / `NO_EDGE`

- **LEAD_SIGNAL**: lead IC／pre-enter 對齊成立 · causal 未 HIT  
- **TIP_LAG_BLOCK**: 仍無 lead 可因果化（對照 0k9n）

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tip_lead_decision_stagea.py
```

Register: **0k9o**
