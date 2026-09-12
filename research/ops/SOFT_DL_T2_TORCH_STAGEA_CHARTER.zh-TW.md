# Soft-Assist DL T2 Torch Stage A — 研究憲章（僅 paper）

日期：2026-09-12  
狀態：**PAPER STAGE A DONE** · 判決 **`RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`**  
母憲章：`SOFT_DL_T2_SEQ_STAGEA`（numpy toehold = **`RULE_PROMOTE_ONLY_NO_T2_LIFT`**）

腳本：`scripts/e16_soft_dl_t2_torch_stagea_screen.py`

## 問題

用 **torch CPU** 的淺層 **TCN／tiny LSTM**（因果過去 L 日 log-return）做 Soft **buy** 加成，能否 tip-MDD 衛生並 **promote-shaped** 勝過 Soft observe？

## 設計摘要

- L∈{10,20} · walk-forward 年切 · 前瞻 10 日報酬回歸 · α∈{0.25,0.5}  
- Sell 固定 observe `RSI6_GT80`；一書搭配規則 `SELL_a05`  
- 不接 live · 不換 Soft／Sleeve observe · 不融合 · 不再加深同一套 binary Soft-buy MLP

## Label

`SOFT_DL_T2_TORCH_STAGEA_CHARTER_2026-09-12__RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`
