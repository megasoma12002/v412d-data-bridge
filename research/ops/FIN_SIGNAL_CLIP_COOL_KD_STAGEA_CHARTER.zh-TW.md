# FIN 訊號改善 Stage A — C_CLIP／D_COOL／B_KD（紙上）

日期：2026-09-26  
狀態：**Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · 不進 live  
父件：成交 A–D deep dive + FIN tip/sealed `FIN_BOTH_WEAK`  
人話：改善訊號本身 → **三軌都研究**（紙上；不 batch 改 live）

## 問題

在 Exact T+1 不動的前提下，紙上挑戰：

1. **C_CLIP** — 收／放 FIN hi 能不能改善 FIN 成交距離  
2. **D_COOL** — 關掉或放寬 COOL floor 能不能改善 FIN 成交且 NAV 可接受  
3. **B_KD** — 放寬 buy_ok 或淡季禁買 FIN 能不能改善 FIN 成交  

## 禁止

改 Exact T+1、改 tip、改 live Soft-Frozen／COOL／KD、從本 Stage A 一次上線三軌。

## 閘門

- 成交：sealed 2023+ FIN BUY adj ±5d 相對 base 改善 ≥ **0.25pp**  
- NAV：heldout MDD 改善 ≥ **−0.50pp** 且 CAGR giveback ≤ **0.50pp**  

複現：`PYTHONPATH=scripts python3 scripts/fin_signal_clip_cool_kd_stagea.py`
