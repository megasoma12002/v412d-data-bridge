# FIN×SAT 分歧切換規則 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_MDD_ONLY`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9l 分歧 Episode **`TIP_MDD_ONLY`** — SAT_LEAD 內 Crisis／SELL↑；crisis→SAT_LEAD IC 強；單狀態切仍 tip CAGR−
- 0k9i tip-gap — `r0050_63` 過熱領先；單門檻不夠
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 研究分歧切換規則層（過熱進入 + Crisis/SELL 確認 + 明確退出）能否 tip-clean · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_DIV_RULE_STAGEA_CHARTER_2026-09-28__DONE_TIP_MDD_ONLY__NO_LIVE_WIRE`

## Why

特徵／episode 已對；binding 缺口在 **規則層**。  
Belief: 分開 **進入／確認／退出** 比單一門檻更能對齊 tip HARD 拖累。  
Risk: 仍 tip CAGR−；或過度待在 SAT 傷 held。

## Mechanism（預註冊有限規則 ≤6 switch）

訊號皆 lag-1 · 每日擇一 COMP／SAT（非加權）· **不擴特徵表**。

| 元件 | 定義 |
|---|---|
| 過熱 `HOT` | `r0050_63_l1` > 全樣本中位 |
| 確認 `CONF` | `crisis_l1` 或 `comp_sells_21_l1` > 中位 |
| 分歧 `DIV` | `trail_rel_63_l1 ≤ −0.01`（0k9l θ） |
| 冷卻 `COOL5` | `r0050_63_l1` ≤ 中位 連續 ≥5 日 |
| 恢復 `REC` | `trail_rel_63_l1 ≥ 0` |

| ID | fam | 規則 |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `R_DIV_ONLY` | switch | DIV → SAT else COMP |
| `R_HOT_AND_CONF` | switch | HOT∧CONF → SAT else COMP |
| `R_ENTER_EXIT` | switch | 進：HOT∧CONF；出：COOL5∨REC；其間保持 |
| `R_DIV_CONF_HOLD` | switch | 進：DIV∧CONF；出：REC；min-hold 21 |
| `R_CRISIS_HOLD21` | switch | 進：crisis；出：非 crisis 連續 5；min-hold 21 |
| `R_HOT_THEN_DIV` | switch | 進：HOT 後 21 日內出現 DIV；出：REC |

## Gates (HIT)

tip-clean + held CAGR↑≥+0.10 + vs SAT +0.05 · `switch` only.

## Verdicts

`RULE_HIT` / `TIP_CLEAN_SOFT` / `TIP_MDD_ONLY` / `NO_EDGE`

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_div_rule_stagea.py
```

Register: **0k9m**
