# Soft-Assist DL T2 極小 Causal Transformer Stage A — 研究憲章（僅 paper）

日期：2026-09-12  
狀態：**PAPER STAGE A OPEN**  
母憲章：`SOFT_DL_T2_TORCH_STAGEA`／`SOFT_DL_T2_SEQ_STAGEA`（TCN／LSTM + numpy 均 **no lift**）

腳本：`scripts/e16_soft_dl_t2_transformer_stagea_screen.py`

## 問題

用 **極小 causal Transformer**（`d_model=8`／`nhead=2`／`nlayers=1`）對過去 L 日 log-return 做 Soft **buy** 加成，能否 tip-MDD 衛生並 **promote-shaped** 勝過 Soft observe（對照 Soft observe + 規則 `SELL_a05`）？

## 設計摘要

- L∈{10,20} · walk-forward 年切 · 前瞻 10 日報酬回歸 · α∈{0.25,0.5}  
- Sell 固定 observe `RSI6_GT80`；一書搭配規則 `SELL_a05`  
- 不接 live · 不換 Soft／Sleeve observe · 不融合 · 不再加深同一套 binary Soft-buy MLP

## Label

`SOFT_DL_T2_TRANSFORMER_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`
