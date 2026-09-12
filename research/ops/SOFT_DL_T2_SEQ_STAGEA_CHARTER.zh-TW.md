# Soft-Assist DL T2 序列 Stage A — 研究憲章（僅 paper）

日期：2026-09-12  
狀態：**PAPER STAGE A DONE** · 判決 **`RULE_PROMOTE_ONLY_NO_T2_LIFT`** · **不接 live** · **不 Soft×Sleeve 融合** · Soft／Sleeve OPEN 選票 **不變**  
母憲章：`SOFT_DL_4TRACK_STAGEA`（T2 曾為 **CHARTER_ONLY_NO_TORCH**）

腳本：`scripts/e16_soft_dl_t2_seq_stagea_screen.py`

## 問題

用 **因果過去 L 日 log-return 序列**（flatten 線性／tiny MLP／淺層 numpy 1D-CNN）做 Soft **buy** 加成，能否通過 tip-MDD 衛生並 **promote-shaped** 勝過 Soft observe？本腳本 **不依賴 torch**。

## 設計摘要

- L∈{10,20} · walk-forward 年切 · 前瞻 10 日報酬回歸 · α∈{0.25,0.5}  
- Sell 固定 observe `RSI6_GT80`（隔離 buy）；一書搭配規則 `SELL_a05`  
- 不接 live · 不換 Soft／Sleeve observe · 不融合 · 不再加深同一套 binary Soft-buy MLP

## Label

`SOFT_DL_T2_SEQ_STAGEA_CHARTER_2026-09-12__RULE_PROMOTE_ONLY_NO_T2_LIFT`
