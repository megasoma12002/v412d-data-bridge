# Soft-Assist Tiny-MLP Stage A — 研究章程（僅 paper）

日期：2026-09-12  
狀態：**PAPER STAGE A DONE** · 判決 **`BEATS_LIVE_NO_OBSERVE_LIFT`** · **不接 live** · **禁止 Soft×Sleeve 融合** · Soft-assist observe **KEEP**  
人類：有辦法試試看深度學習嗎

腳本：`scripts/e16_soft_dl_mlp_stagea_screen.py`  
Screen：`SOFT_DL_MLP_STAGEA_SCREEN.md`

## 問題

純 numpy 的**小型 MLP**（`feat→8→1`）以 walk-forward 訓練，在 live `KD_OPT` 上做加分 Soft buy，是否能 tip-clean／promote-shaped 勝過 `LIVE_KD_OPT` 或抬升 Soft-assist observe？

## 誠實邊界

這是 **DL 試水**（淺層 NN），不是 LSTM／Transformer，也不是 live-ready。

## 非動作

不接 live、不換 Soft-assist observe、不合體、不重開硬 AND。

詳見英文章程。
